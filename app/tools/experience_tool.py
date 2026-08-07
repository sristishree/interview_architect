import logging
from typing import List

from langchain_core.tools import tool

from app.knowledge_base.store import QuestionStore
from app.models.question import GeneratedQuestionList

logger = logging.getLogger(__name__)
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

    prompt = f"""Generate {remaining} behavioral interview questions about a candidate's experience at:
{company_role}

Focus on:
- Impact and ownership at this company
- Challenges specific to that environment
- Growth and learning during the tenure
- Cross-functional or stakeholder dynamics

Tags should be 3-5 relevant keywords."""

    try:
        llm = get_llm(fast=True).with_structured_output(GeneratedQuestionList, method="json_schema")
        result = llm.invoke(prompt)
        llm_questions = [q.model_dump() for q in result.questions]
    except Exception as e:
        logger.warning("experience_tool LLM call failed: %s", e)
        llm_questions = []

    return (kb_results + llm_questions)[:n]
