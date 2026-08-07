from fastapi import APIRouter, HTTPException

from app.db import SessionStore

router = APIRouter(prefix="/sessions", tags=["sessions"])
_store = SessionStore()


@router.get("")
def list_sessions():
    return _store.list_sessions()


@router.get("/{session_id}")
def get_session(session_id: int):
    session = _store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
