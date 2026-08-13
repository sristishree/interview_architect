import logging
import os
from typing import List

from langchain_core.tools import tool

from app.models.question import GeneratedQuestionList

logger = logging.getLogger(__name__)


@tool
def search_and_generate_questions(
    topic: str, n: int = 3, difficulty: str = "Medium"
) -> List[dict]:
    """
    Search the web for a topic and use an LLM to convert the results into
    structured interview questions.

    Args:
        topic: The technical topic to search for.
        n: Number of questions to generate.
        difficulty: Target difficulty — 'Easy', 'Medium', or 'Hard'.
    """
    from app.knowledge_base.store import QuestionStore

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    from tavily import TavilyClient
    client = TavilyClient(api_key=api_key)
    response = client.search(query=f"{topic} interview questions technical")
    snippets = "\n".join(
        r.get("content", "")[:300] for r in response.get("results", [])[:5]
    )

    known_categories = QuestionStore().categories()
    category_hint = (
        f"Use one of these existing categories if it fits: {', '.join(known_categories)}. "
        "If none fits, coin a short PascalCase name (e.g. 'VoiceAI', 'TabularGeneration')."
    )

    prompt = (
        f"Generate {n} technical interview questions about '{topic}' at {difficulty} difficulty.\n"
        f"Use these search results as inspiration:\n\n{snippets}\n\n"
        f"Each question must be clear, specific, and answerable in an interview setting. "
        f"Tags should be 3-5 relevant keywords.\n"
        f"Category guidance: {category_hint}"
    )

    try:
        from app.config import get_structured_llm
        result = get_structured_llm(GeneratedQuestionList, fast=True).invoke(prompt)
        return [q.model_dump() for q in result.questions]
    except Exception as e:
        logger.warning("web_search_tool LLM call failed: %s", e)
        return []
