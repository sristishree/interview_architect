import logging
from typing import List

from langchain_core.tools import tool

from app.models.question import GeneratedQuestionList

logger = logging.getLogger(__name__)


@tool
def get_experience_questions(
    company_role: str, n: int = 3, difficulty: str = "Medium"
) -> List[dict]:
    """
    Generate deep probing questions anchored to a candidate's specific work experience entry.
    Verifies actual involvement, technical depth, and validity of impact claims.

    Args:
        company_role: Encoded work experience string from the planner, e.g.:
            "Perfios (Lead Data Scientist, 3yr) — Responsibilities: Built X; Designed Y; Led Z"
        n: Number of questions to return.
        difficulty: 'Easy', 'Medium', or 'Hard'.
    """

    prompt = f"""You are a senior technical interviewer probing a candidate's actual depth and involvement in their stated work experience.

Work experience entry:
{company_role}

Difficulty: {difficulty}

Generate {n} targeted interview questions. Your goal is to distinguish candidates who genuinely owned and deeply understood their work from those who were peripheral or are overstating their contributions.

RULES:
1. Every question MUST anchor to a specific responsibility or claim from the entry above — quote or paraphrase it explicitly in the question stem.
2. Do NOT ask generic behavioral questions (e.g. "Tell me about a challenge"). Every question must require knowledge that only someone who personally implemented or designed the work would have.
3. Cover these angles across your {n} questions:
   - IMPLEMENTATION DEPTH (question_type = "implementation"): Ask HOW they built or implemented a specific thing they claimed. Expect the candidate to walk through architecture, key decisions, and trade-offs. E.g. "You mention building X — walk me through the design: what components did you build, what did you choose off-the-shelf, and why?"
   - TECHNICAL KNOWLEDGE (question_type = "theory"): Probe whether they understand the underlying concepts of a tool or method they listed. E.g. "You used Y — what are its failure modes / when would you NOT use it?"
   - OWNERSHIP VERIFICATION (question_type = "behavioral"): Clarify the candidate's specific role vs. the team. E.g. "For Z, were you the primary designer, or were you implementing someone else's design? What specifically did you decide?"
   - IMPACT CHALLENGE (if metrics appear): Challenge the measurement. E.g. "You say you improved X by 40% — how was the baseline established and what was the exact measurement methodology?"

4. For follow_up: add a sharper follow-up that probes the weakest assumption in the question — the thing a candidate could bluff through without.

Tags should be 3-5 technical keywords from the specific work described (not generic terms like "machine learning")."""

    try:
        from app.config import get_structured_llm
        result = get_structured_llm(GeneratedQuestionList, fast=True).invoke(prompt)
        return [q.model_dump() for q in result.questions][:n]
    except Exception as e:
        logger.warning("experience_tool LLM call failed: %s", e)
        return []
