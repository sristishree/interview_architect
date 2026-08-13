"""
Interview Planner Agent
-----------------------
The most important reasoning step. Given the candidate profile, project details,
and work experience details:
  1. Decides total question count (15-25 based on seniority)
  2. Resolves difficulty (dynamic by experience, overridden by user if set)
  3. Allocates ~50% of questions to project-sourced topics with rich context
  4. Allocates ~30% to work experience topics that probe actual involvement and depth
  5. Specifies question type mix per topic (implementation, design, theory, behavioral, etc.)

This planning trace is the most valuable thing to inspect in LangSmith.
Uses LITELLM_MODEL (default: gpt-4o) for the strategic reasoning required.
"""

import json
from typing import TYPE_CHECKING, Optional

from app.config import get_structured_llm
from app.models.plan import InterviewPlan
from app.models.resume import CandidateProfile

if TYPE_CHECKING:
    from app.graph.state import InterviewState


_SYSTEM = """You are a principal engineer designing a technical interview for a specific candidate.

You receive three inputs:
  1. candidate_profile — enriched profile with seniority, key skills, domains
  2. projects — structured list of actual resume projects (title, tech_stack, description, details)
  3. work_experiences — structured list of work experience entries (name, role, duration_years, responsibilities)

Create an InterviewPlan following these rules:

QUESTION COUNT
- Junior/Mid: 15  |  Senior: 18  |  Lead/Principal: 22

DIFFICULTY
- Use candidate_profile.suggested_difficulty unless difficulty_override is provided.

ALLOCATION — target ~50% from projects, ~30% from work experience, ~20% skills/leadership

── PROJECT TOPICS (source = "project") — ~50% of total ──────────────────────────────
For each major project (those with substantial tech_stack or details), create one TopicPlan:
  source = "project"
  topic  = "<title> — Stack: <comma-joined tech_stack> — <one-sentence description>"
           Example: "Credit Risk ML — Stack: XGBoost, Airflow, Python — Daily scoring pipeline for 500K loan applications"
  n_questions = 3–5 depending on project complexity
  question_types: {design: 1, implementation: 2, optimization: 1}  (adjust to project nature)

── WORK EXPERIENCE TOPICS (source = "experience") — ~30% of total ───────────────────
For each work experience entry that has ≥2 responsibilities listed, create one TopicPlan:
  source = "experience"
  topic  = "<Company> (<Role>, <duration>yr) — Responsibilities: <semicolon-joined list of the 4–6 most specific and technical bullet points>"
           Example: "Perfios (Lead Data Scientist, 3yr) — Responsibilities: Built distributed ML training pipeline using PyTorch FSDP; Designed feature store reducing latency by 40%; Led A/B testing framework serving 1B requests/day; Migrated monolith to microservices on Kubernetes"
  n_questions = 3–4
  question_types: {implementation: 2, theory: 1, behavioral: 1}

  The questions generated from these topics must:
  - Probe the candidate's ACTUAL depth and ownership of the stated work (not generic behavioral)
  - Verify they understand the tools/methods they claim to have used
  - Challenge any specific metrics or impact claims in the responsibilities
  - Ask what they'd do differently — probing real experience vs. surface knowledge

── SKILL / LEADERSHIP TOPICS (source = "skill" or "leadership") — ~20% ─────────────
- Core skill from interview_focus: 2–3 questions  {implementation: 2, theory: 1}
- Leadership/behavioral for Senior+: 2 questions  (source = "leadership", topic = "Leadership")

REASONING
- Explain WHY you made allocation decisions for this specific candidate.
- A 6yr Lead DS who built prod ML systems gets hard system-design questions, not basic Python.
- Work experience topics must be distinct from project topics — don't repeat the same work twice."""

_llm = get_structured_llm(InterviewPlan)


def plan_interview_node(state: "InterviewState") -> dict:
    profile = CandidateProfile.model_validate(state["candidate_profile"])
    difficulty_override: Optional[str] = state.get("difficulty_override")

    override_note = (
        f"\nUser has overridden difficulty to: {difficulty_override}"
        if difficulty_override
        else "\nNo difficulty override — use suggested_difficulty from the profile."
    )

    projects_json = json.dumps(
        [p.model_dump() for p in profile.projects], indent=2
    )

    work_experiences_json = json.dumps(
        [w.model_dump() for w in profile.work_experiences], indent=2
    )

    result: InterviewPlan = _llm.invoke([
        ("system", _SYSTEM),
        ("human", (
            f"Candidate profile:\n{profile.model_dump_json(indent=2)}\n\n"
            f"Projects (use these for ~50% of the topic plans):\n{projects_json}\n\n"
            f"Work experiences (use these for ~30% of the topic plans — probe the responsibilities deeply):\n{work_experiences_json}"
            f"{override_note}"
        )),
    ])
    return {"interview_plan": result.model_dump()}
