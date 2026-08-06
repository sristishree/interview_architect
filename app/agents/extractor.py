"""
Profile Extractor Agent
-----------------------
This is where reasoning starts. Takes the raw parsed resume and infers:
  - Role and domains
  - Core skills and projects (structured)
  - Seniority and interview focus

Structured output strategy:
  - CandidateProfile.model_json_schema() produces the JSON schema from the Pydantic model.
  - with_structured_output(_schema, method="json_schema") passes it to the API as
    response_format={"type": "json_schema", "json_schema": {...}} — not function calling.
  - The LLM is forced to return valid JSON matching the schema.
  - We validate the returned dict back into CandidateProfile for type safety.

Uses LITELLM_MODEL (default: gpt-4o) for the inference quality required.
"""

from typing import TYPE_CHECKING

from app.config import get_llm
from app.models.resume import CandidateProfile, ParsedResume

if TYPE_CHECKING:
    from app.graph.state import InterviewState


_SYSTEM = """You are a senior technical interviewer building an enriched candidate profile from a parsed resume.

The parsed resume already contains raw extracted data (skills, projects, companies, experience_years).
Your job is to REASON over that data — not re-copy it. Each field description in the schema tells
you exactly what to produce for that field.

Cross-field rules that the schema cannot express:
- role: if ParsedResume.role is missing or too vague (e.g. just "Engineer"), infer the most
  accurate title from the companies, projects, and skills sections.
- seniority: title beats years when they conflict — a 5yr "Lead Engineer" is Lead, not Senior.
- key_skills: only pick skills that appear in ParsedResume.skills. Do not invent new ones.

Do not invent information not present in the resume."""

# Generate the JSON schema from the Pydantic model.
# This is exactly what gets sent to the API as response_format — inspect it to
# see the constraints the LLM must satisfy.
_schema = CandidateProfile.model_json_schema()

# method="json_schema"  → uses OpenAI's structured outputs (response_format), not function calling.
# Passing the schema dict (not the class) makes the flow explicit:
#   LLM returns a plain dict → we validate it into CandidateProfile below.
_llm = get_llm().with_structured_output(_schema, method="json_schema")


def extract_profile_node(state: "InterviewState") -> dict:
    parsed = ParsedResume.model_validate(state["parsed_resume"])

    result_dict: dict = _llm.invoke([
        ("system", _SYSTEM),
        ("human", (
            f"Analyse this parsed resume and build the candidate profile:\n\n"
            f"{parsed.model_dump_json(indent=2)}"
        )),
    ])

    # Validate the dict into the Pydantic model — catches any schema violations at runtime.
    result = CandidateProfile.model_validate(result_dict)

    # Pin years_of_experience from the parser — the LLM was told to copy it, but
    # we enforce it here to prevent any drift or hallucination.
    result.years_of_experience = parsed.experience_years

    return {"candidate_profile": result.model_dump()}
