from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Company(BaseModel):
    name: str
    role: str
    duration_years: Optional[float] = None

class Project(BaseModel):
    title: str
    description: str
    tech_stack: List[str]
    details: List[str]


class ParsedResume(BaseModel):
    """Raw extraction from the resume. No inference — only what is explicitly written."""
    name: str
    role: Optional[str] = Field(description="Job title if mentioned in resume header or about/summary seciont")
    experience_years: float = Field(description="""Total professional experience in years, either clearly 
    mentioned by the candidate in their about/summary section or the resume header, or it is to be calculated
    as the total of the durations mentioned in the  work experiences""")
    skills: List[str] = Field(description="""The skills mentioned by the candidate in the skills sections.
    If there is no skills section, return an empty list""")
    projects: List[Project] = Field(description="""Extract all the projects mentioned by the candidate in the projects
    section. The projects should be returned as a list of list.
    - Multiple projects should be extracted as separate items of the list
    - The bullet points or details of each project should be extracted as items of the project list item""")
    companies: List[Company] = Field(description="Employers' names with role and duration of work there rounded to years")
    raw_text: str = Field(description="Full resume text for downstream use")

class CandidateProfile(BaseModel):
    """
    Enriched profile produced by the extractor agent.

    Split into two groups:
    - Pass-through: name, role, years_of_experience — sourced from ParsedResume, pinned in the node.
    - Inferred: everything else — requires LLM reasoning over the resume.
    """
    # ── Pass-through (pinned from ParsedResume in the node, not LLM-generated) ──
    name: str
    role: str = Field(description="Normalized job title — inferred if the header is missing or ambiguous")
    years_of_experience: float = Field(description="Pinned from ParsedResume.experience_years in the node")

    # ── Inferred ─────────────────────────────────────────────────────────────────
    domains: List[str] = Field(
        description="Broad engineering domains the candidate operates in: ML Engineering, Backend, LLMs, Cloud, Frontend etc."
    )
    key_skills: List[str] = Field(
        description=(
            "Curated shortlist of 4–8 individual skills most worth probing in the interview. "
            "Pick from ParsedResume.skills — prioritise depth over breadth. "
            "These are passed directly to get_skill_questions(), so use plain names: 'XGBoost', not 'Tree-based ML'."
        )
    )
    project_themes: List[str] = Field(
        description=(
            "Recurring technical themes inferred across all projects. "
            "E.g. 'Production NLP', 'Credit Risk ML', 'RAG Pipelines'. "
            "These inform what depth of questions to ask about the candidate's projects."
        )
    )
    seniority: Literal["Junior", "Mid", "Senior", "Lead", "Principal"] = Field(
        description=(
            "Junior (<2yr) | Mid (2–4yr) | Senior (4–7yr) | "
            "Lead (explicit lead/staff title, or 7+yr without a senior cap) | "
            "Principal (explicit principal/director/VP title)"
        )
    )
    interview_focus: List[str] = Field(
        description=(
            "4–6 specific topic names ordered by interview priority. "
            "Draw from key_skills and project_themes - be precise: 'XGBoost' not 'ML', "
            "'LLM system design' not 'AI'."
        )
    )
    suggested_difficulty: Literal["Easy", "Medium", "Hard"] = Field(
        description="Easy (<2yr) | Medium (2–5yr) | Hard (5+yr)"
    )
