"""
Interview Planner Agent
-----------------------
The most important reasoning step. Given the candidate profile, project details,
and work experience details:
  1. Computes total question count deterministically (Python function, not LLM):
       base(seniority: 8–16) + skill_bonus(≤5) + project_bonus(≤8) + experience_bonus(≤6), capped at 30.
       Full mode: question_count_override takes precedence if provided.
       Focused mode: uses focus_config.question_count exactly.
  2. Resolves difficulty (dynamic by experience, overridden by user if set)
  3. Full mode: allocates ~50% to projects, ~30% to work experience, ~20% to skills/leadership
  4. Focused mode: allocates 100% to the requested section, honours type filter and modifier
  5. Specifies question type mix per topic (implementation, design, theory, behavioral, etc.)

This planning trace is the most valuable thing to inspect in LangSmith.
Uses OPENROUTER_MODEL (default: openai/gpt-4o) for the strategic reasoning required.
"""

import json
from typing import TYPE_CHECKING, List, Optional

from app.config import get_structured_llm
from app.models.focus import FocusConfig, InterviewMode, ResumeSection
from app.models.plan import InterviewPlan
from app.models.resume import CandidateProfile

if TYPE_CHECKING:
    from app.graph.state import InterviewState


_SENIORITY_BASE = {
    "Junior": 8,
    "Mid": 10,
    "Senior": 12,
    "Lead": 14,
    "Principal": 16,
}
_MAX_QUESTIONS = 30


def _compute_question_count(profile: CandidateProfile) -> int:
    base = _SENIORITY_BASE.get(profile.seniority, 10)

    skill_bonus = min(len(profile.skills) // 3, 5)

    project_bonus = min(
        sum(1 for p in profile.projects if p.tech_stack or p.details) * 2,
        8,
    )

    experience_bonus = min(
        sum(
            2 if len(w.responsibilities) >= 3 else 1 if len(w.responsibilities) == 2 else 0
            for w in profile.work_experiences
        ),
        6,
    )

    return min(base + skill_bonus + project_bonus + experience_bonus, _MAX_QUESTIONS)


_SYSTEM_FULL = """You are a principal engineer designing a technical interview for a specific candidate.

You receive four inputs:
  1. candidate_profile — enriched profile with seniority, key skills, domains
  2. projects — structured list of actual resume projects (title, tech_stack, description, details)
  3. work_experiences — structured list of work experience entries (name, role, duration_years, responsibilities)
  4. total_questions — pre-computed integer; use this exact number, do not change it

Create an InterviewPlan following these rules:

QUESTION COUNT
- Use total_questions exactly as given. Do not add or subtract from it.

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
  n_questions = 3–4
  question_types: {implementation: 2, theory: 1, behavioral: 1}

── SKILL / LEADERSHIP TOPICS (source = "skill" or "leadership") — ~20% ─────────────
- Core skill from interview_focus: 2–3 questions  {implementation: 2, theory: 1}
- Leadership/behavioral for Senior+: 2 questions  (source = "leadership", topic = "Leadership")

REASONING
- Explain WHY you made allocation decisions for this specific candidate.
- Work experience topics must be distinct from project topics — don't repeat the same work twice."""

_SYSTEM_FOCUSED = """You are a principal engineer designing a focused interview targeting one specific resume section.

You receive:
  1. candidate_profile — enriched profile
  2. section_data — the content of the requested section (projects, work_experiences, or skills list)
  3. total_questions — exact count to generate; do not change it
  4. focus_section — which section to target: "work_experience" | "projects" | "skills"
  5. question_types_filter — list of allowed question types, or empty (all types allowed)
  6. modifier — optional free-text thematic constraint (soft guidance only)

RULES:
- Allocate ALL total_questions to the focus_section. Do not add topics from other sections.
- Source mapping: work_experience → "experience", projects → "project", skills → "skill"
- If question_types_filter is non-empty, every TopicPlan.question_types must use ONLY those types
- If modifier is set, use it as a thematic constraint in topic descriptions and question_types weighting
- Distribute questions across the items in section_data (e.g. one TopicPlan per project)
- DIFFICULTY: use candidate_profile.suggested_difficulty unless difficulty_override is provided

REASONING: explain which items you allocated to and why."""

_llm = get_structured_llm(InterviewPlan)


def plan_interview_node(state: "InterviewState") -> dict:
    profile = CandidateProfile.model_validate(state["candidate_profile"])
    interview_mode: str = state.get("interview_mode", InterviewMode.FULL)
    focus_dict = state.get("focus_config")
    difficulty_override: Optional[str] = state.get("difficulty_override")

    override_note = (
        f"\ndifficulty_override: {difficulty_override}"
        if difficulty_override
        else "\nNo difficulty override — use suggested_difficulty from profile."
    )

    if interview_mode == InterviewMode.FOCUSED and focus_dict:
        focus = FocusConfig.model_validate(focus_dict)
        total_questions = focus.question_count if focus.question_count is not None else _compute_question_count(profile)

        section_data = _get_section_data(profile, focus.section)
        types_filter = [qt.value for qt in focus.question_types] if focus.question_types else []

        result: InterviewPlan = _llm.invoke([
            ("system", _SYSTEM_FOCUSED),
            ("human", (
                f"total_questions: {total_questions}\n"
                f"focus_section: {focus.section.value}\n"
                f"question_types_filter: {types_filter or 'all types allowed'}\n"
                f"modifier: {focus.modifier or 'none'}\n"
                f"{override_note}\n\n"
                f"Candidate profile:\n{profile.model_dump_json(indent=2)}\n\n"
                f"Section data ({focus.section.value}):\n{json.dumps(section_data, indent=2)}"
            )),
        ])
    else:
        # Full mode — compute question count
        if state.get("question_count_override"):
            total_questions = state["question_count_override"]
        else:
            total_questions = _compute_question_count(profile)

        projects_json = json.dumps([p.model_dump() for p in profile.projects], indent=2)
        work_experiences_json = json.dumps([w.model_dump() for w in profile.work_experiences], indent=2)

        result: InterviewPlan = _llm.invoke([
            ("system", _SYSTEM_FULL),
            ("human", (
                f"total_questions: {total_questions}\n"
                f"{override_note}\n\n"
                f"Candidate profile:\n{profile.model_dump_json(indent=2)}\n\n"
                f"Projects (use these for ~50% of the topic plans):\n{projects_json}\n\n"
                f"Work experiences (use these for ~30% of the topic plans):\n{work_experiences_json}"
            )),
        ])

    return {"interview_plan": result.model_dump()}


def _get_section_data(profile: CandidateProfile, section: ResumeSection) -> list:
    if section == ResumeSection.PROJECTS:
        return [p.model_dump() for p in profile.projects]
    if section == ResumeSection.WORK_EXPERIENCE:
        return [w.model_dump() for w in profile.work_experiences]
    return profile.skills  # SKILLS
