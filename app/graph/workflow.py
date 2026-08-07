"""
LangGraph workflow for the Interview Architect.

Graph topology:
    START
      │
      ▼
  parse_resume          (Resume Parser Agent — extraction only)
      │
      ▼
  extract_profile       (Profile Extractor Agent — infers domains, seniority)
      │
      ▼
  plan_interview        (Interview Planner Agent — strategic question allocation, ~60% from projects)
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

Every node run is a separate span in LangSmith. The planner's reasoning
and the curator's curation notes are the most valuable traces to inspect.
"""

import math

from langgraph.graph import END, START, StateGraph

from app.agents.curator import curate_interview_node
from app.agents.extractor import extract_profile_node
from app.agents.parser import parse_resume_node
from app.agents.planner import plan_interview_node
from app.graph.state import InterviewState
from app.models.plan import InterviewPlan

_MAX_RETRIEVAL_ATTEMPTS = 2


def retrieve_questions_node(state: InterviewState) -> dict:
    """
    Deterministic retrieval node — not an LLM agent.
    On first run, fetches n_questions per topic plan.
    On retries (shortfall > 0), distributes the shortfall proportionally across all topics.
    """
    from app.tools.experience_tool import get_experience_questions
    from app.tools.project_tool import get_project_questions
    from app.tools.skill_tool import get_skill_questions

    plan = InterviewPlan.model_validate(state["interview_plan"])
    shortfall: int = state.get("shortfall", 0)
    attempt: int = state.get("retrieval_attempts", 0)

    # On retry: distribute shortfall evenly across topics (min 1 per topic)
    if shortfall > 0:
        per_topic = max(1, math.ceil(shortfall / len(plan.topic_plans)))
        topic_counts = {tp.topic: per_topic for tp in plan.topic_plans}
    else:
        topic_counts = {tp.topic: tp.n_questions for tp in plan.topic_plans}

    all_questions: list[dict] = list(state.get("retrieved_questions", []))

    for topic_plan in plan.topic_plans:
        n = topic_counts[topic_plan.topic]
        source = topic_plan.source.lower()

        if source in ("skill", "leadership"):
            results = get_skill_questions.invoke({
                "skill": topic_plan.topic,
                "n": n,
                "difficulty": topic_plan.difficulty,
            })
        elif source == "project":
            results = get_project_questions.invoke({
                "project_description": topic_plan.topic,
                "n": n,
                "difficulty": topic_plan.difficulty,
            })
        elif source == "experience":
            results = get_experience_questions.invoke({
                "company_role": topic_plan.topic,
                "n": n,
                "difficulty": topic_plan.difficulty,
            })
        else:
            results = get_skill_questions.invoke({
                "skill": topic_plan.topic,
                "n": n,
                "difficulty": topic_plan.difficulty,
            })

        all_questions.extend(results or [])

    return {
        "retrieved_questions": all_questions,
        "retrieval_attempts": attempt + 1,
    }


def _after_parse(state: InterviewState) -> str:
    parsed = state.get("parsed_resume") or {}
    if not parsed.get("is_resume", True):
        return "abort"
    return "extract_profile"


def _should_retry_retrieval(state: InterviewState) -> str:
    if (
        state.get("shortfall", 0) > 0
        and state.get("retrieval_attempts", 0) < _MAX_RETRIEVAL_ATTEMPTS
    ):
        return "retrieve_questions"
    return END


def _abort_node(state: InterviewState) -> dict:
    return {"error": "The uploaded document does not appear to be a resume or CV."}


def build_graph() -> StateGraph:
    builder = StateGraph(InterviewState)

    builder.add_node("parse_resume", parse_resume_node)
    builder.add_node("abort", _abort_node)
    builder.add_node("extract_profile", extract_profile_node)
    builder.add_node("plan_interview", plan_interview_node)
    builder.add_node("retrieve_questions", retrieve_questions_node)
    builder.add_node("curate_interview", curate_interview_node)

    builder.add_edge(START, "parse_resume")
    builder.add_conditional_edges("parse_resume", _after_parse, {"abort": "abort", "extract_profile": "extract_profile"})
    builder.add_edge("abort", END)
    builder.add_edge("extract_profile", "plan_interview")
    builder.add_edge("plan_interview", "retrieve_questions")
    builder.add_edge("retrieve_questions", "curate_interview")
    builder.add_conditional_edges("curate_interview", _should_retry_retrieval)

    return builder.compile()
