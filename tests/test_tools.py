"""
Unit tests for retrieval tools.
The skill_tool is tested against the real KB (no LLM).
project_tool and experience_tool make LLM calls — marked as integration tests.
"""
import pytest

from app.tools.skill_tool import get_skill_questions


def test_skill_tool_returns_list():
    result = get_skill_questions.invoke({"skill": "Python", "n": 3})
    assert isinstance(result, list)


def test_skill_tool_respects_n():
    result = get_skill_questions.invoke({"skill": "SQL", "n": 2})
    assert len(result) <= 2


def test_skill_tool_hard_difficulty():
    result = get_skill_questions.invoke({"skill": "XGBoost", "n": 5, "difficulty": "Hard"})
    for q in result:
        assert q["difficulty"] == "Hard"


def test_skill_tool_easy_difficulty():
    result = get_skill_questions.invoke({"skill": "Python", "n": 5, "difficulty": "Easy"})
    for q in result:
        assert q["difficulty"] == "Easy"


def test_skill_tool_returns_question_fields():
    result = get_skill_questions.invoke({"skill": "Machine Learning", "n": 2})
    for q in result:
        assert "question" in q
        assert "topic" in q
        assert "difficulty" in q
        assert "tags" in q


def test_skill_tool_unknown_topic_returns_empty():
    result = get_skill_questions.invoke({"skill": "zxqwerty_fake_topic_123", "n": 3})
    assert isinstance(result, list)


@pytest.mark.integration
def test_project_tool_generates_questions():
    from app.tools.project_tool import get_project_questions
    result = get_project_questions.invoke({
        "project_description": "Address Matching System — NLP-based fuzzy address deduplication",
        "n": 3,
        "difficulty": "Hard",
    })
    assert isinstance(result, list)
    assert len(result) > 0
    assert all("question" in q for q in result)


@pytest.mark.integration
def test_experience_tool_generates_questions():
    from app.tools.experience_tool import get_experience_questions
    result = get_experience_questions.invoke({
        "company_role": "Perfios — Lead Data Scientist",
        "n": 2,
        "difficulty": "Hard",
    })
    assert isinstance(result, list)
    assert len(result) > 0
