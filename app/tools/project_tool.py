import logging
from typing import List

from langchain_core.tools import tool

from app.knowledge_base.store import QuestionStore
from app.models.question import GeneratedQuestionList

logger = logging.getLogger(__name__)
_store = QuestionStore()


@tool
def get_project_questions(
    project_description: str, n: int = 4, difficulty: str = "Medium"
) -> List[dict]:
    """
    Generate project-specific interview questions. First searches the KB for
    related questions, then uses an LLM to generate questions tailored to the
    specific project.

    Args:
        project_description: Short description of the project (name + key details).
        n: Number of questions to return.
        difficulty: 'Easy', 'Medium', or 'Hard'.
    """

    kb_results = _store.search(topic=project_description, n=max(2, n // 2), difficulty=difficulty)
    remaining = max(1, n - len(kb_results))

    prompt = f"""Generate {remaining} specific technical interview questions for this project:

Project: {project_description}
Difficulty: {difficulty}

Focus on:
- Implementation decisions the candidate actually made
- Design trade-offs and alternatives considered
- Evaluation methodology and production challenges
- What they would do differently

Tags should be 3-5 keywords relevant to the project."""

    try:
        from app.config import get_structured_llm
        result = get_structured_llm(GeneratedQuestionList, fast=True).invoke(prompt)
        llm_questions = [q.model_dump() for q in result.questions]
    except Exception as e:
        logger.warning("project_tool LLM call failed: %s", e)
        llm_questions = []

    return (kb_results + llm_questions)[:n]
