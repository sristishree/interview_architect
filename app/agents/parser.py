"""
Resume Parser Agent
-------------------
Pure extraction — no reasoning, no inference.
Reads PDF/DOCX/TXT and returns a structured ParsedResume.
Uses LITELLM_MODEL_FAST (default: gpt-4o-mini) since this is an extraction-only task.
"""

import os
from typing import TYPE_CHECKING

from app.config import get_llm
from app.models.resume import ParsedResume

if TYPE_CHECKING:
    from app.graph.state import InterviewState


def _read_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        import pypdf
        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
    elif ext == ".docx":
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


_SYSTEM = """You are a resume parser. Extract ONLY what is explicitly stated.
Do NOT infer, add, or assume information not present in the text.
For experience_years: sum durations from the dates given. If dates are missing, use context clues but note the uncertainty.
For skills, projects, companies, education: include all items as written — do not clean, merge, or expand them."""

_llm = get_llm(fast=True).with_structured_output(ParsedResume)


def parse_resume_node(state: "InterviewState") -> dict:
    raw_text = _read_file(state["resume_path"])
    result: ParsedResume = _llm.invoke([
        ("system", _SYSTEM),
        ("human", f"Parse this resume:\n\n{raw_text}"),
    ])
    result.raw_text = raw_text
    return {"parsed_resume": result.model_dump()}
