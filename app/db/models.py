from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Run inputs ────────────────────────────────────────────────────────────
    resume_path: Mapped[str] = mapped_column(String)
    difficulty_override: Mapped[str | None] = mapped_column(String, nullable=True)

    # ── Scalar summary (for list view) ────────────────────────────────────────
    candidate_name: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_difficulty: Mapped[str | None] = mapped_column(String, nullable=True)
    total_questions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Full pipeline artifacts (for detail view) ─────────────────────────────
    parsed_resume_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_set_json: Mapped[str | None] = mapped_column(Text, nullable=True)
