import json
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from langgraph_sdk import get_client

from api.schemas import RunCreatedResponse, RunStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])

_NODE_LABELS = {
    "parse_resume":       "Parsing resume",
    "extract_profile":    "Extracting candidate profile",
    "plan_interview":     "Planning interview",
    "retrieve_questions": "Retrieving questions",
    "curate_interview":   "Curating final question set",
}

UPLOAD_DIR = Path("data/uploads")
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")
ASSISTANT_ID = "interview_architect"


def _graph_input(resume_path: str, difficulty_override: Optional[str] = None) -> dict:
    return {
        "resume_path": resume_path,
        "difficulty_override": difficulty_override,
        "retrieved_questions": [],
        "retrieval_attempts": 0,
        "shortfall": 0,
    }


@router.post("", response_model=RunCreatedResponse, status_code=202)
async def create_interview(
    file: Optional[UploadFile] = File(default=None),
    resume_path: Optional[str] = Form(default=None),
    difficulty_override: Optional[str] = Form(default=None),
):
    """
    Start an interview generation run.

    Send either:
    - multipart/form-data with a `file` field (PDF, DOCX, or TXT)
    - multipart/form-data with a `resume_path` field pointing to a file on the server

    Returns a thread_id + run_id to poll with GET /interview/{thread_id}/{run_id}.
    """
    if file is None and resume_path is None:
        raise HTTPException(status_code=422, detail="Provide either 'file' or 'resume_path'")

    if file is not None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename).suffix if file.filename else ".txt"
        dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
        dest.write_bytes(await file.read())
        path = str(dest.resolve())
    else:
        resolved = Path(resume_path).expanduser().resolve()
        if not resolved.exists():
            raise HTTPException(status_code=422, detail=f"File not found: {resume_path}")
        path = str(resolved)

    client = get_client(url=LANGGRAPH_URL)
    thread = await client.threads.create()
    run = await client.runs.create(
        thread_id=thread["thread_id"],
        assistant_id=ASSISTANT_ID,
        input=_graph_input(path, difficulty_override),
    )

    return RunCreatedResponse(
        thread_id=thread["thread_id"],
        run_id=run["run_id"],
        status=run["status"],
    )


@router.get("/{thread_id}/{run_id}", response_model=RunStatusResponse)
async def get_interview_status(thread_id: str, run_id: str):
    """
    Poll run status.

    Possible statuses: pending | running | success | error

    On success, `result` contains:
    - interview_set: the final structured question set
    - candidate_profile: inferred domains, seniority, focus areas
    - interview_plan: topic allocation and reasoning
    """
    client = get_client(url=LANGGRAPH_URL)

    try:
        run = await client.runs.get(thread_id, run_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    result = None
    error = None

    if run["status"] == "success":
        state = await client.threads.get_state(thread_id)
        values = state["values"]
        result = {
            "interview_set": values.get("interview_set"),
            "candidate_profile": values.get("candidate_profile"),
            "interview_plan": values.get("interview_plan"),
        }
    elif run["status"] == "error":
        try:
            state = await client.threads.get_state(thread_id)
            error = state["values"].get("error", "Unknown error")
        except Exception:
            error = "Unknown error"

    return RunStatusResponse(
        thread_id=thread_id,
        run_id=run_id,
        status=run["status"],
        result=result,
        error=error,
    )


@router.delete("/{thread_id}/{run_id}", status_code=204)
async def cancel_interview(thread_id: str, run_id: str):
    """Cancel a running interview generation."""
    client = get_client(url=LANGGRAPH_URL)
    try:
        await client.runs.cancel(thread_id, run_id)
    except Exception:
        pass  # Already completed or not found — treat as success


@router.get("/{thread_id}/{run_id}/stream")
async def stream_interview_status(thread_id: str, run_id: str):
    """
    SSE stream for a running interview. Emits:
      {"type": "progress", "node": "<name>", "label": "<human label>"}  — one per completed node
      {"type": "done",     "result": {...}}                              — run complete
      {"type": "error",    "message": "..."}                            — run failed
    """
    async def generate():
        client = get_client(url=LANGGRAPH_URL)
        try:
            async for chunk in client.runs.join_stream(
                thread_id, run_id, stream_mode="updates"
            ):
                if chunk.event != "updates" or not isinstance(chunk.data, dict):
                    continue
                for node_name in chunk.data:
                    if node_name not in _NODE_LABELS:
                        continue
                    payload = {"type": "progress", "node": node_name, "label": _NODE_LABELS[node_name]}
                    yield f"data: {json.dumps(payload)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return

        # Stream exhausted — fetch final state and always persist
        try:
            from app.db import SessionStore

            run = await client.runs.get(thread_id, run_id)
            run_status = run["status"]

            try:
                state = await client.threads.get_state(thread_id)
                values = dict(state["values"])
            except Exception:
                values = {}

            # Ensure every run (including graph-level failures) is saved to DB
            if run_status == "error" and not values.get("error"):
                values["error"] = "Run failed during processing"
            SessionStore().save_if_new(thread_id, values)

            if run_status != "success":
                msg = values.get("error") or f"Run ended with status: {run_status}"
                yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
                return

            if values.get("error") or not values.get("interview_set"):
                msg = values.get("error") or "Run completed but produced no interview set"
                yield f"data: {json.dumps({'type': 'error', 'message': msg})}\n\n"
                return

            result = {
                "interview_set": values.get("interview_set"),
                "candidate_profile": values.get("candidate_profile"),
                "interview_plan": values.get("interview_plan"),
            }
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
