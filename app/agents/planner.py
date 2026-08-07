"""
Interview Planner Agent
-----------------------
The most important reasoning step. Given the candidate profile and actual project details:
  1. Decides total question count (15-25 based on seniority)
  2. Resolves difficulty (dynamic by experience, overridden by user if set)
  3. Allocates ~60% of questions to project-sourced topics with rich context
  4. Specifies question type mix per topic (implementation, design, theory, etc.)

This planning trace is the most valuable thing to inspect in LangSmith.
Uses LITELLM_MODEL (default: gpt-4o) for the strategic reasoning required.
"""

import json
from typing import TYPE_CHECKING, Optional

from app.config import get_llm
from app.models.plan import InterviewPlan
from app.models.resume import CandidateProfile, ParsedResume

if TYPE_CHECKING:
    from app.graph.state import InterviewState


_SYSTEM = """You are a principal engineer designing a technical interview for a specific candidate.

You receive two inputs:
  1. candidate_profile — enriched profile with seniority, key skills, domains
  2. projects — structured list of actual resume projects (title, tech_stack, description, details)

Create an InterviewPlan following these rules:

QUESTION COUNT
- Junior/Mid: 15  |  Senior: 18  |  Lead/Principal: 22

DIFFICULTY
- Use candidate_profile.suggested_difficulty unless difficulty_override is provided.

ALLOCATION — target ~60% of total_questions from project sources
- For each major project (those with substantial tech_stack or details), create one TopicPlan:
    source = "project"
    topic  = "<title> — Stack: <comma-joined tech_stack> — <one-sentence description>"
             Example: "Credit Risk ML — Stack: XGBoost, Airflow, Python — Daily scoring pipeline for 500K loan applications"
    n_questions = 3–5 depending on project complexity
    question_types: {design: 1, implementation: 2, optimization: 1}  (adjust to project nature)
- Remaining ~40%: core skills, behavioral/leadership (Senior+), light experience probing

SKILL TOPICS (source = "skill" or "leadership")
- Core skill from interview_focus: 3–4 questions  {implementation: 2, theory: 1}
- Secondary skill: 1–2 questions
- Leadership/behavioral for Senior+: 2–3 questions  (source = "leadership", topic = "Leadership")

EXPERIENCE TOPIC (source = "experience") — only if the candidate has distinct industry stints
- 1–2 questions  {behavioral: N}

REASONING
- Explain WHY you made allocation decisions for this specific candidate.
- A 6yr Lead DS who built prod ML systems gets hard system-design questions, not basic Python."""

_llm = get_llm().with_structured_output(InterviewPlan, method="json_schema")


def plan_interview_node(state: "InterviewState") -> dict:
    profile = CandidateProfile.model_validate(state["candidate_profile"])
    parsed = ParsedResume.model_validate(state["parsed_resume"])
    difficulty_override: Optional[str] = state.get("difficulty_override")

    override_note = (
        f"\nUser has overridden difficulty to: {difficulty_override}"
        if difficulty_override
        else "\nNo difficulty override — use suggested_difficulty from the profile."
    )

    projects_json = json.dumps(
        [p.model_dump() for p in parsed.projects], indent=2
    )

    result: InterviewPlan = _llm.invoke([
        ("system", _SYSTEM),
        ("human", (
            f"Candidate profile:\n{profile.model_dump_json(indent=2)}\n\n"
            f"Projects (use these to build ~60% of the topic plans):\n{projects_json}"
            f"{override_note}"
        )),
    ])
    return {"interview_plan": result.model_dump()}
