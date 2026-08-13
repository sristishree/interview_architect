"""
Question Curator Agent
----------------------
Receives all retrieved questions (potentially 3-5x more than needed) and:
  1. Pre-filters by question_type if a focus_config type filter is active
  2. Removes exact and semantic duplicates
  3. Ensures diversity — no two questions that ask essentially the same thing
  4. Selects the best questions respecting the plan's allocation
  5. Orders them into interview sections (warm-up → depth → leadership)
  6. Estimates total interview duration
  7. Returns shortfall so the graph can loop back for more if dedup removed too many

Uses LITELLM_MODEL (default: gpt-4o) since curation requires judgment about question quality.
"""

import json
from typing import TYPE_CHECKING, List, Optional

from app.config import get_structured_llm
from app.models.focus import FocusConfig
from app.models.plan import InterviewPlan
from app.models.question import InterviewSet
from app.models.resume import CandidateProfile

if TYPE_CHECKING:
    from app.graph.state import InterviewState


_SYSTEM = """You are a senior interviewer curating a final interview question set.

Given:
- The candidate profile
- The interview plan (with allocation targets per topic)
- All retrieved questions (may contain duplicates and more than needed)

Your job:
1. Remove duplicates — questions asking essentially semantically the same thing keep only the best version
2. Respect allocation — stay close to n_questions per topic from the plan
3. Group into sections — each InterviewSection has a name and ordered list of questions
4. Order within sections — easier/warm-up questions first, harder ones later
5. Order sections — technical depth before leadership/behavioral
6. Estimate duration — assume 4 min/implementation, 3 min/theory, 5 min/design, 4 min/behavioral

Return a complete InterviewSet with all fields filled.
curator_notes: 1-2 sentences on any tradeoffs you made (e.g. "Dropped 3 Python basics, focused on async and GIL given senior level")."""

_llm = get_structured_llm(InterviewSet)


def curate_interview_node(state: "InterviewState") -> dict:
    profile = CandidateProfile.model_validate(state["candidate_profile"])
    plan = InterviewPlan.model_validate(state["interview_plan"])
    questions: List[dict] = list(state["retrieved_questions"])

    # Pre-filter by type if a focus type filter is active — enforces the constraint
    # before the LLM sees the questions so the curator can't accidentally include
    # type-mismatched ones. Dropped questions count toward shortfall → retry loop.
    allowed_types: Optional[set] = None
    focus_dict = state.get("focus_config")
    if focus_dict:
        focus = FocusConfig.model_validate(focus_dict)
        if focus.question_types:
            allowed_types = {qt.value for qt in focus.question_types}

    if allowed_types:
        questions = [q for q in questions if q.get("question_type") in allowed_types]

    result: InterviewSet = _llm.invoke([
        ("system", _SYSTEM),
        ("human", (
            f"Candidate profile:\n{profile.model_dump_json(indent=2)}\n\n"
            f"Interview plan:\n{plan.model_dump_json(indent=2)}\n\n"
            f"Retrieved questions ({len(questions)} total):\n"
            f"{json.dumps(questions, indent=2)}"
        )),
    ])

    shortfall = max(0, plan.total_questions - result.total_questions)
    return {
        "interview_set": result.model_dump(),
        "shortfall": shortfall,
    }
