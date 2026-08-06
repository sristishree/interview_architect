from typing import List

from langchain_core.tools import tool

from app.knowledge_base.store import QuestionStore
from app.models.question import GeneratedQuestionList

_store = QuestionStore()


@tool
def get_experience_questions(
    company_role: str, n: int = 3, difficulty: str = "Medium"
) -> List[dict]:
    """
    Generate questions that probe a candidate's work experience at a specific
    company/role. Blends KB behavioral questions with LLM-generated contextual ones.

    Args:
        company_role: Company and role, e.g. 'Fractal Analytics — Data Scientist'.
        n: Number of questions to return.
        difficulty: 'Easy', 'Medium', or 'Hard'.
    """
    from app.config import get_llm

    kb_results = _store.search(
        topic="Leadership", n=max(1, n // 2), difficulty=difficulty, category="Leadership"
    )

    remaining = max(1, n - len(kb_results))
    llm = get_llm(fast=True).with_structured_output(GeneratedQuestionList)

    prompt = f"""Generate {remaining} behavioral interview questions about a candidate's experience at:
{company_role}

Focus on:
- Impact and ownership at this company
- Challenges specific to that environment
- Growth and learning during the tenure
- Cross-functional or stakeholder dynamics

Tags should be 3-5 relevant keywords."""

    generated = llm.invoke(prompt)
    combined = kb_results + [q.model_dump() for q in generated.questions]
    return combined[:n]
