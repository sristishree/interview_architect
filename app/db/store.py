import json
import os
from datetime import datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, InterviewSession

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "sessions.db"
)


class SessionStore:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        engine = create_engine(f"sqlite:///{os.path.abspath(db_path)}")
        Base.metadata.create_all(engine)
        _migrate(engine)
        self._Session = sessionmaker(bind=engine)

    def save(self, state: dict, thread_id: str | None = None) -> int:
        """Persist a completed pipeline state. Returns the new session ID."""
        interview_set = state.get("interview_set") or None

        record = InterviewSession(
            created_at=datetime.utcnow(),
            thread_id=thread_id,
            resume_path=state.get("resume_path", ""),
            difficulty_override=state.get("difficulty_override"),
            candidate_name=interview_set.get("candidate_name") if interview_set else None,
            resolved_difficulty=interview_set.get("resolved_difficulty") if interview_set else None,
            total_questions=interview_set.get("total_questions") if interview_set else None,
            estimated_duration_minutes=interview_set.get("estimated_duration_minutes") if interview_set else None,
            error=state.get("error"),
            parsed_resume_json=_dump(state.get("parsed_resume")),
            candidate_profile_json=_dump(state.get("candidate_profile")),
            interview_plan_json=_dump(state.get("interview_plan")),
            interview_set_json=_dump(interview_set),
        )

        with self._Session() as session:
            session.add(record)
            session.commit()
            return record.id

    def save_if_new(self, thread_id: str, state: dict) -> int | None:
        """Save only if this thread_id hasn't been persisted yet. Returns session ID or None."""
        with self._Session() as session:
            exists = session.query(InterviewSession).filter_by(thread_id=thread_id).first()
            if exists:
                return None
        return self.save(state, thread_id=thread_id)

    def list_sessions(self) -> list[dict]:
        """Return summary rows for all sessions, newest first. Incomplete rows are marked failed."""
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


def _migrate(engine) -> None:
    """Add any columns/indexes that exist in the model but not yet in the DB."""
    existing_cols = {col["name"] for col in inspect(engine).get_columns("interview_sessions")}
    with engine.begin() as conn:
        if "thread_id" not in existing_cols:
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN thread_id VARCHAR"))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_interview_sessions_thread_id "
                "ON interview_sessions (thread_id) WHERE thread_id IS NOT NULL"
            ))
        if "error" not in existing_cols:
            conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN error TEXT"))


def _dump(obj) -> str | None:
    if obj is None:
        return None
    return json.dumps(obj) if not isinstance(obj, str) else obj


def _to_summary(row: InterviewSession) -> dict:
    failed = not row.interview_set_json or row.interview_set_json in ("{}", "null")
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "candidate_name": row.candidate_name,
        "resume_path": row.resume_path,
        "difficulty_override": row.difficulty_override,
        "resolved_difficulty": row.resolved_difficulty,
        "total_questions": row.total_questions,
        "estimated_duration_minutes": row.estimated_duration_minutes,
        "failed": failed,
        "error": row.error,
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
