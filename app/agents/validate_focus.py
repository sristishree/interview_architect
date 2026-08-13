"""
Focus Validator
---------------
Deterministic node — no LLM call.

Checks whether the section the user requested in focus_config actually has
content in the extracted CandidateProfile. If not, falls back silently to
Full Interview mode and sets a fallback_notice for the frontend banner.
"""

from typing import TYPE_CHECKING

from app.models.focus import FocusConfig, InterviewMode, ResumeSection
from app.models.resume import CandidateProfile

if TYPE_CHECKING:
    from app.graph.state import InterviewState

_SECTION_FIELD: dict[ResumeSection, str] = {
    ResumeSection.WORK_EXPERIENCE: "work_experiences",
    ResumeSection.PROJECTS: "projects",
    ResumeSection.SKILLS: "skills",
}


def validate_focus_node(state: "InterviewState") -> dict:
    focus_dict = state.get("focus_config")

    if not focus_dict:
        return {"interview_mode": InterviewMode.FULL}

    focus = FocusConfig.model_validate(focus_dict)
    profile = CandidateProfile.model_validate(state["candidate_profile"])

    field = _SECTION_FIELD[focus.section]
    has_content = bool(getattr(profile, field, None))

    if not has_content:
        return {
            "interview_mode": InterviewMode.FULL,
            "focus_config": None,
            "fallback_notice": (
                "Selected section not found in resume — generated full interview instead."
            ),
        }

    return {"interview_mode": InterviewMode.FOCUSED}
