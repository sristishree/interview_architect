"""
Profile Builder
---------------
Single LLM node that replaces the old parse_resume + extract_profile two-step.

Input:  state["raw_text"] — plain text extracted by the text_extractor node (no LLM).
Output: state["candidate_profile"] — fully populated CandidateProfile.

The model schema is divided into two groups that the LLM handles in a single pass:

  VERBATIM EXTRACTION — copy exactly what is written in the resume:
    is_resume, name, years_of_experience, skills, projects, work_experiences

  INFERRED ENRICHMENT — reason over the extracted data:
    role, domains, key_skills, project_themes, seniority, interview_focus, suggested_difficulty

Uses the stronger model (LITELLM_MODEL / gpt-4o) since it must both extract accurately
and infer correctly in one shot.
"""

from typing import TYPE_CHECKING

from app.config import get_structured_llm
from app.models.resume import CandidateProfile

if TYPE_CHECKING:
    from app.graph.state import InterviewState

_SYSTEM = """You are building a complete candidate profile from raw resume text in a single pass.

Your output has two parts — handle both together:

PART 1 — VERBATIM EXTRACTION (copy exactly what is written, no inference)
- is_resume: True only if the document has at least one of: work experience, education, or a skills section
- name: candidate's full name
- years_of_experience: stated in the header/summary, or summed from work_experiences if not stated
- skills: list every skill from the skills section verbatim; empty list if no skills section
- projects: every project from the projects section — title, description, tech_stack, and every detail bullet verbatim
- work_experiences: every employer entry — name, role, duration (rounded years), and every responsibility bullet verbatim; do not paraphrase

PART 2 — INFERRED ENRICHMENT (reason over the data above)
- role: normalise the current/most recent title; infer from work_experiences if the header is missing or vague
- domains: broad engineering areas the candidate works in (ML Engineering, Backend, LLMs, Cloud, etc.)
- key_skills: 4–8 skills most worth probing in an interview — pick from the skills list, prioritise depth
- project_themes: recurring technical themes across all projects (e.g. 'Production NLP', 'Credit Risk ML')
- seniority: Junior (<2yr) | Mid (2–4yr) | Senior (4–7yr) | Lead (lead/staff title or 7+yr) | Principal — title beats years
- interview_focus: 4–6 specific topics in priority order; be precise ('XGBoost' not 'ML', 'LLM system design' not 'AI')
- suggested_difficulty: Easy (<2yr) | Medium (2–5yr) | Hard (5+yr)

Rules:
- Do not invent information not present in the resume.
- Responsibilities under work_experiences must be copied verbatim — every bullet point, nothing paraphrased."""

_llm = get_structured_llm(CandidateProfile)


def build_profile_node(state: "InterviewState") -> dict:
    raw_text: str = state["raw_text"]
    result: CandidateProfile = _llm.invoke([
        ("system", _SYSTEM),
        ("human", f"Build the complete candidate profile from this resume text:\n\n{raw_text}"),
    ])
    return {"candidate_profile": result.model_dump()}
