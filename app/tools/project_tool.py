import logging
from typing import List, Optional

from langchain_core.tools import tool

from app.knowledge_base.store import QuestionStore
from app.models.question import GeneratedQuestionList

logger = logging.getLogger(__name__)
_store = QuestionStore()


@tool
def get_project_questions(
    project_description: str,
    n: int = 4,
    difficulty: str = "Medium",
    question_types: Optional[List[str]] = None,
) -> List[dict]:
    """
    Generate project-specific interview questions. First searches the KB for
    related questions, then uses an LLM to generate questions tailored to the
    specific project.

    Args:
        project_description: Short description of the project (name + key details).
        n: Number of questions to return.
        difficulty: 'Easy', 'Medium', or 'Hard'.
        question_types: Optional list of allowed question types, e.g. ['design', 'implementation'].
    """
    kb_results = _store.search(
        topic=project_description, n=max(2, n // 2), difficulty=difficulty, question_types=question_types
    )
    remaining = max(1, n - len(kb_results))

    type_constraint = (
        f"\nOnly generate question types from: {', '.join(question_types)}" if question_types else ""
    )

    prompt = f"""Generate {remaining} specific technical interview questions for this project:

Project: {project_description}
Difficulty: {difficulty}

Focus on:
- Implementation decisions the candidate actually made
- Design trade-offs and alternatives considered
- Evaluation methodology and production challenges
- What they would do differently
{type_constraint}

Tags should be 3-5 keywords relevant to the project."""

    try:
        from app.config import get_structured_llm
        result = get_structured_llm(GeneratedQuestionList, fast=True).invoke(prompt)
        llm_questions = [q.model_dump() for q in result.questions]
    except Exception as e:
        logger.warning("project_tool LLM call failed: %s", e)
        llm_questions = []

    return (kb_results + llm_questions)[:n]
