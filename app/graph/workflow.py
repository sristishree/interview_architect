"""
LangGraph workflow for the Interview Architect.

Graph topology:
    START
      │
      ▼
  extract_text          (Text Extractor — pypdf / PaddleOCR, no LLM)
      │
      ├── empty text ──► abort
      │
      ▼
  build_profile         (Profile Builder — single LLM call → merged CandidateProfile)
      │
      ├── is_resume=False ──► abort
      │
      ▼
  validate_focus        (Focus Validator — deterministic; checks section content)
      │
      ▼
  plan_interview        (Interview Planner — full or focused allocation)
      │
      ▼
  retrieve_questions ◄──────────────────────────────────┐
      │                                                  │
      ▼                                                  │
  curate_interview      (dedup + order + section)        │
      │                                                  │
      ├─── shortfall > 0 and attempts < 2 ───────────────┘
      │
      └─── shortfall == 0 or max retries ───► END
"""

import math
from typing import List, Optional

from langgraph.graph import END, START, StateGraph

from app.agents.curator import curate_interview_node
from app.agents.profile_builder import build_profile_node
from app.agents.text_extractor import extract_text_node
from app.agents.planner import plan_interview_node
from app.agents.validate_focus import validate_focus_node
from app.graph.state import InterviewState
from app.models.plan import InterviewPlan

_MAX_RETRIEVAL_ATTEMPTS = 2


def retrieve_questions_node(state: InterviewState) -> dict:
    """
    Deterministic retrieval node — not an LLM agent.
    On first run, fetches n_questions per topic plan.
    On retries (shortfall > 0), distributes the shortfall proportionally across all topics.
    Passes question_types filter through to tools when focus_config specifies one.
    """
    from app.tools.experience_tool import get_experience_questions
    from app.tools.project_tool import get_project_questions
    from app.tools.skill_tool import get_skill_questions

    plan = InterviewPlan.model_validate(state["interview_plan"])
    shortfall: int = state.get("shortfall", 0)
    attempt: int = state.get("retrieval_attempts", 0)

    # Resolve question_types filter from focus_config (None = no filter)
    focus_dict = state.get("focus_config")
    question_types: Optional[List[str]] = None
    if focus_dict:
        qt = focus_dict.get("question_types")
        if qt:
            question_types = qt

    if shortfall > 0:
        per_topic = max(1, math.ceil(shortfall / len(plan.topic_plans)))
        topic_counts = {tp.topic: per_topic for tp in plan.topic_plans}
    else:
        topic_counts = {tp.topic: tp.n_questions for tp in plan.topic_plans}

    all_questions: list[dict] = list(state.get("retrieved_questions", []))

    for topic_plan in plan.topic_plans:
        n = topic_counts[topic_plan.topic]
        source = topic_plan.source.lower()
        base_args = {"n": n, "difficulty": topic_plan.difficulty}
        if question_types:
            base_args["question_types"] = question_types

        if source in ("skill", "leadership"):
            results = get_skill_questions.invoke({"skill": topic_plan.topic, **base_args})
        elif source == "project":
            results = get_project_questions.invoke({"project_description": topic_plan.topic, **base_args})
        elif source == "experience":
            results = get_experience_questions.invoke({"company_role": topic_plan.topic, **base_args})
        else:
            results = get_skill_questions.invoke({"skill": topic_plan.topic, **base_args})

        all_questions.extend(results or [])

    return {
        "retrieved_questions": all_questions,
        "retrieval_attempts": attempt + 1,
    }


def _after_extract(state: InterviewState) -> str:
    if not (state.get("raw_text") or "").strip():
        return "abort"
    return "build_profile"


def _after_build(state: InterviewState) -> str:
    profile = state.get("candidate_profile") or {}
    if not profile.get("is_resume", True):
        return "abort"
    return "validate_focus"


def _should_retry_retrieval(state: InterviewState) -> str:
    if (
        state.get("shortfall", 0) > 0
        and state.get("retrieval_attempts", 0) < _MAX_RETRIEVAL_ATTEMPTS
    ):
        return "retrieve_questions"
    return END


def _abort_node(state: InterviewState) -> dict:
    raw_text = (state.get("raw_text") or "").strip()
    if not raw_text:
        return {"error": "Could not extract any text from the uploaded file."}
    return {"error": "The uploaded document does not appear to be a resume or CV."}


def build_graph() -> StateGraph:
    builder = StateGraph(InterviewState)

    builder.add_node("extract_text", extract_text_node)
    builder.add_node("abort", _abort_node)
    builder.add_node("build_profile", build_profile_node)
    builder.add_node("validate_focus", validate_focus_node)
    builder.add_node("plan_interview", plan_interview_node)
    builder.add_node("retrieve_questions", retrieve_questions_node)
    builder.add_node("curate_interview", curate_interview_node)

    builder.add_edge(START, "extract_text")
    builder.add_conditional_edges("extract_text", _after_extract, {"abort": "abort", "build_profile": "build_profile"})
    builder.add_conditional_edges("build_profile", _after_build, {"abort": "abort", "validate_focus": "validate_focus"})
    builder.add_edge("abort", END)
    builder.add_edge("validate_focus", "plan_interview")
    builder.add_edge("plan_interview", "retrieve_questions")
    builder.add_edge("retrieve_questions", "curate_interview")
    builder.add_conditional_edges("curate_interview", _should_retry_retrieval)

    return builder.compile()
