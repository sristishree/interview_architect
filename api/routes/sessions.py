import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.db import SessionStore

router = APIRouter(prefix="/sessions", tags=["sessions"])
_store = SessionStore()


@router.get("")
def list_sessions():
    return _store.list_sessions()


@router.get("/{session_id}/resume")
def get_resume(session_id: int):
    session = _store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    path = Path(session["resume_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(str(path), media_type=media_type or "application/octet-stream")


@router.get("/{session_id}")
def get_session(session_id: int):
    session = _store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
