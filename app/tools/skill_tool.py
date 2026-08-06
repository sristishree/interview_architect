from typing import List, Optional

from langchain_core.tools import tool

from app.knowledge_base.store import QuestionStore

_store = QuestionStore()


@tool
def get_skill_questions(skill: str, n: int = 5, difficulty: Optional[str] = None) -> List[dict]:
    """
    Retrieve interview questions for a specific skill from the knowledge base.
    Falls back to web search (via web_search_tool) when fewer than n//2 results are found.

    Args:
        skill: Skill name, e.g. 'Python', 'XGBoost', 'SQL', 'Docker'.
        n: Number of questions to return.
        difficulty: Optional filter — 'Easy', 'Medium', or 'Hard'.
    """
    results = _store.search(topic=skill, n=n, difficulty=difficulty)

    if len(results) < max(1, n // 2):
        try:
            from app.tools.web_search_tool import search_and_generate_questions
            extra = search_and_generate_questions.invoke(
                {"topic": skill, "n": n - len(results), "difficulty": difficulty or "Medium"}
            )
            _store.add(extra)
            results = _store.search(topic=skill, n=n, difficulty=difficulty)
        except Exception:
            pass  # Tavily key not set or network error — return what we have

    return results
