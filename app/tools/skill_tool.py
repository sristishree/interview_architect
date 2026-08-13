import logging
from typing import List, Optional

from langchain_core.tools import tool

from app.knowledge_base.store import QuestionStore
from app.models.question import GeneratedQuestionList

logger = logging.getLogger(__name__)
_store = QuestionStore()


@tool
def get_skill_questions(skill: str, n: int = 5, difficulty: Optional[str] = None) -> List[dict]:
    """
    Retrieve interview questions for a specific skill from the knowledge base.
    Falls back to LLM generation when fewer than n//2 relevant results are found.

    Args:
        skill: Skill name, e.g. 'Python', 'XGBoost', 'SQL', 'Docker'.
        n: Number of questions to return.
        difficulty: Optional filter — 'Easy', 'Medium', or 'Hard'.
    """

    resolved_difficulty = difficulty or "Medium"
    kb_results = _store.search(topic=skill, n=max(2, n // 2), difficulty=difficulty)
    remaining = max(1, n - len(kb_results))

    if remaining > 0:
        prompt = (
            f"Generate {remaining} technical interview questions specifically about '{skill}'.\n"
            f"Difficulty: {resolved_difficulty}\n\n"
            f"Rules:\n"
            f"- Every question must be directly and specifically about '{skill}' — not general programming.\n"
            f"- Set the topic field to '{skill}'.\n"
            f"- Tags should be 3-5 keywords directly related to '{skill}'.\n"
            f"- Focus on practical knowledge, common pitfalls, and real-world usage of '{skill}'."
        )
        try:
            from app.config import get_structured_llm
            result = get_structured_llm(GeneratedQuestionList, fast=True).invoke(prompt)
            llm_questions = [q.model_dump() for q in result.questions]
        except Exception as e:
            logger.warning("skill_tool LLM call failed for '%s': %s", skill, e)
            llm_questions = []
    else:
        llm_questions = []

    logger.info("skill_tool '%s': KB=%d, LLM=%d", skill[:40], len(kb_results), len(llm_questions))
    return (kb_results + llm_questions)[:n]
