from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    name: str
    role: str
    duration_years: Optional[float] = None
    responsibilities: List[str] = Field(
        default_factory=list,
        description=(
            "Every bullet point, responsibility, or achievement explicitly listed under this role — "
            "copy verbatim, do not paraphrase or merge entries"
        )
    )


class Project(BaseModel):
    title: str
    description: str
    tech_stack: List[str]
    details: List[str]


class CandidateProfile(BaseModel):
    """
    Complete candidate profile produced by a single LLM call over raw resume text.

    Contains both verbatim extraction (what the resume says) and inferred enrichments
    (what the resume implies). Text is extracted by a separate OCR/pypdf node before
    this model is populated — no LLM is used in the text extraction step.
    """

    # ── Validation ───────────────────────────────────────────────────────────
    is_resume: bool = Field(
        description=(
            "True if the document is clearly a professional resume or CV — "
            "it must have at least one of: work experience, education, or a skills section. "
            "False for any other document (article, invoice, code file, random text, etc.)."
        )
    )

    # ── Verbatim extraction ──────────────────────────────────────────────────
    name: str
    years_of_experience: float = Field(
        description=(
            "Total professional experience in years. "
            "Take from the resume header/summary if stated; otherwise sum durations from work_experiences."
        )
    )
    skills: List[str] = Field(
        description="All skills listed in the dedicated skills section. Empty list if no skills section."
    )
    projects: List[Project] = Field(
        description=(
            "All projects from the projects section. "
            "Each entry: title, description, tech_stack, and details (every bullet point verbatim)."
        )
    )
    work_experiences: List[WorkExperience] = Field(
        description=(
            "All work experience entries in order. For each: employer name, role, duration in years (rounded), "
            "and every bullet point listed under that role copied verbatim — do not paraphrase."
        )
    )

    # ── Inferred enrichments ─────────────────────────────────────────────────
    role: str = Field(
        description=(
            "Normalised current or most recent job title. "
            "Take from the resume header if clear; otherwise infer from work_experiences and projects."
        )
    )
    domains: List[str] = Field(
        description="Broad engineering domains the candidate operates in: ML Engineering, Backend, LLMs, Cloud, Frontend, etc."
    )
    key_skills: List[str] = Field(
        description=(
            "Curated shortlist of 4–8 skills most worth probing in the interview. "
            "Pick from the skills list — prioritise depth over breadth. "
            "Use plain names: 'XGBoost', not 'Tree-based ML'."
        )
    )
    project_themes: List[str] = Field(
        description=(
            "Recurring technical themes inferred across all projects. "
            "E.g. 'Production NLP', 'Credit Risk ML', 'RAG Pipelines'."
        )
    )
    seniority: Literal["Junior", "Mid", "Senior", "Lead", "Principal"] = Field(
        description=(
            "Junior (<2yr) | Mid (2–4yr) | Senior (4–7yr) | "
            "Lead (explicit lead/staff title, or 7+yr) | Principal (explicit principal/director/VP title). "
            "Title beats years when they conflict."
        )
    )
    interview_focus: List[str] = Field(
        description=(
            "4–6 specific topic names ordered by interview priority. "
            "Draw from key_skills and project_themes. Be precise: 'XGBoost' not 'ML', "
            "'LLM system design' not 'AI'."
        )
    )
    suggested_difficulty: Literal["Easy", "Medium", "Hard"] = Field(
        description="Easy (<2yr) | Medium (2–5yr) | Hard (5+yr)"
    )
