"""Unit tests for the QuestionStore — no LLM calls."""
import pytest

from app.knowledge_base.store import QuestionStore


def test_store_loads_questions(store: QuestionStore):
    assert len(store.questions) > 0, "KB should have seed questions"


def test_store_has_expected_count(store: QuestionStore):
    assert len(store.questions) >= 70, "KB should have at least 70 seed questions"


def test_search_by_exact_topic(store: QuestionStore):
    results = store.search("Python", n=5)
    assert len(results) > 0
    topics = [q["topic"].lower() for q in results]
    assert any("python" in t for t in topics)


def test_search_by_partial_topic(store: QuestionStore):
    results = store.search("XGBoost", n=5)
    assert len(results) > 0


def test_search_by_tag(store: QuestionStore):
    results = store.search("boosting", n=3)
    assert len(results) > 0


def test_difficulty_filter_hard(store: QuestionStore):
    results = store.search("Python", n=10, difficulty="Hard")
    assert all(q["difficulty"] == "Hard" for q in results)


def test_difficulty_filter_easy(store: QuestionStore):
    results = store.search("SQL", n=10, difficulty="Easy")
    assert all(q["difficulty"] == "Easy" for q in results)


def test_search_returns_at_most_n(store: QuestionStore):
    results = store.search("Python", n=3)
    assert len(results) <= 3


def test_unknown_topic_returns_empty_or_few(store: QuestionStore):
    results = store.search("zxqwerty_nonexistent_topic_abc123", n=5)
    assert isinstance(results, list)
    assert len(results) == 0


def test_search_returns_dicts(store: QuestionStore):
    results = store.search("SQL", n=2)
    for q in results:
        assert "question" in q
        assert "difficulty" in q
        assert "id" in q


def test_add_question_persists(tmp_path):
    import json
    import shutil
    from pathlib import Path

    src = Path(__file__).parent.parent / "data" / "questions.json"
    dst = tmp_path / "questions.json"
    shutil.copy(src, dst)

    store = QuestionStore(path=dst)
    original_count = len(store.questions)

    new_q = {
        "topic": "TestTopic",
        "difficulty": "Easy",
        "category": "General",
        "tags": ["test"],
        "question": "Is this a test question?",
        "follow_up": None,
        "question_type": "theory",
    }
    store.add([new_q])

    assert len(store.questions) == original_count + 1
    with open(dst) as f:
        on_disk = json.load(f)
    assert len(on_disk) == original_count + 1
    assert any(q["topic"] == "TestTopic" for q in on_disk)


def test_add_deduplicates_by_id(tmp_path):
    import shutil
    from pathlib import Path

    src = Path(__file__).parent.parent / "data" / "questions.json"
    dst = tmp_path / "questions.json"
    shutil.copy(src, dst)

    store = QuestionStore(path=dst)
    original_count = len(store.questions)

    existing = store.questions[0].copy()
    store.add([existing])  # same id — should be skipped

    assert len(store.questions) == original_count
