import json
import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, InterviewSession

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "sessions.db"
)


class SessionStore:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        engine = create_engine(f"sqlite:///{os.path.abspath(db_path)}")
        Base.metadata.create_all(engine)
        self._Session = sessionmaker(bind=engine)

    def save(self, state: dict) -> int:
        """Persist a completed pipeline state. Returns the new session ID."""
        interview_set = state.get("interview_set") or {}

        record = InterviewSession(
            created_at=datetime.utcnow(),
            resume_path=state.get("resume_path", ""),
            difficulty_override=state.get("difficulty_override"),
            candidate_name=interview_set.get("candidate_name"),
            resolved_difficulty=interview_set.get("resolved_difficulty"),
            total_questions=interview_set.get("total_questions"),
            estimated_duration_minutes=interview_set.get("estimated_duration_minutes"),
            parsed_resume_json=_dump(state.get("parsed_resume")),
            candidate_profile_json=_dump(state.get("candidate_profile")),
            interview_plan_json=_dump(state.get("interview_plan")),
            interview_set_json=_dump(interview_set),
        )

        with self._Session() as session:
            session.add(record)
            session.commit()
            return record.id

    def list_sessions(self) -> list[dict]:
        """Return summary rows suitable for a UI list view, newest first."""
        with self._Session() as session:
            rows = (
                session.query(InterviewSession)
                .order_by(InterviewSession.created_at.desc())
                .all()
            )
            return [_to_summary(r) for r in rows]

    def get_session(self, session_id: int) -> dict | None:
        """Return full detail for one session, or None if not found."""
        with self._Session() as session:
            row = session.get(InterviewSession, session_id)
            if row is None:
                return None
            return _to_detail(row)


def _dump(obj) -> str | None:
    if obj is None:
        return None
    return json.dumps(obj) if not isinstance(obj, str) else obj


def _to_summary(row: InterviewSession) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "candidate_name": row.candidate_name,
        "resume_path": row.resume_path,
        "difficulty_override": row.difficulty_override,
        "resolved_difficulty": row.resolved_difficulty,
        "total_questions": row.total_questions,
        "estimated_duration_minutes": row.estimated_duration_minutes,
    }


def _to_detail(row: InterviewSession) -> dict:
    return {
        **_to_summary(row),
        "parsed_resume": _load(row.parsed_resume_json),
        "candidate_profile": _load(row.candidate_profile_json),
        "interview_plan": _load(row.interview_plan_json),
        "interview_set": _load(row.interview_set_json),
    }


def _load(val: str | None):
    if val is None:
        return None
    return json.loads(val)
