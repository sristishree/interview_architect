import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from langgraph_sdk import get_client

from api.schemas import RunCreatedResponse, RunStatusResponse

router = APIRouter(prefix="/interview", tags=["interview"])

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
