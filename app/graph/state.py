from typing import List, Optional
from typing_extensions import TypedDict


class InterviewState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    resume_path: str
    difficulty_override: Optional[str]      # None = auto-detect from experience

    # ── Stage 1: Text Extractor (pypdf / PaddleOCR, no LLM) ─────────────────
    raw_text: Optional[str]

    # ── Stage 2: Profile Builder (single LLM call) ───────────────────────────
    candidate_profile: Optional[dict]       # CandidateProfile.model_dump()

    # ── Stage 3: Interview Planner ───────────────────────────────────────────
    interview_plan: Optional[dict]          # InterviewPlan.model_dump()

    # ── Stage 4: Retrieval Node (accumulates across retries) ────────────────
    retrieved_questions: List[dict]         # flat list; appended to on each retry
    retrieval_attempts: int                 # incremented each time node runs

    # ── Stage 5: Question Curator ────────────────────────────────────────────
    interview_set: Optional[dict]           # InterviewSet.model_dump()
    shortfall: int                          # questions still needed after dedup; 0 = done

    # ── Error passthrough ────────────────────────────────────────────────────
    error: Optional[str]
