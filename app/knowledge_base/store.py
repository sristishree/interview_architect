import json
import os
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional

_KB_PATH = Path(__file__).parent.parent.parent / "data" / "questions.json"


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class QuestionStore:
    def __init__(self, path: Path = _KB_PATH):
        self.path = path
        with open(path) as f:
            self.questions: List[dict] = json.load(f)

    def _score(self, q: dict, topic: str) -> float:
        topic_lower = topic.lower()
        topic_score = _similarity(q["topic"].lower(), topic_lower)
        tag_score = max((_similarity(t.lower(), topic_lower) for t in q["tags"]), default=0.0)
        return max(topic_score, tag_score * 0.9)

    def search(
        self,
        topic: str,
        n: int = 5,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        question_types: Optional[List[str]] = None,
        min_score: float = 0.6,
    ) -> List[dict]:
        candidates = self.questions

        if difficulty:
            candidates = [q for q in candidates if q["difficulty"] == difficulty]
        if category:
            candidates = [q for q in candidates if q["category"] == category]
        if question_types:
            candidates = [q for q in candidates if q.get("question_type") in question_types]

        scored = [(self._score(q, topic), q) for q in candidates]
        scored = [(s, q) for s, q in scored if s >= min_score]
        scored.sort(key=lambda x: x[0], reverse=True)

        return [q for _, q in scored[:n]]

    def add(self, questions: List[dict]) -> None:
        """Append new questions to the KB and persist to disk."""
        existing_ids = {q["id"] for q in self.questions}
        next_id = max(existing_ids) + 1 if existing_ids else 1

        new = []
        for q in questions:
            if q.get("id") in existing_ids:
                continue
            q["id"] = next_id
            next_id += 1
            new.append(q)

        self.questions.extend(new)
        with open(self.path, "w") as f:
            json.dump(self.questions, f, indent=2)

    def categories(self) -> List[str]:
        """Return the sorted list of distinct category values currently in the KB."""
        return sorted({q["category"] for q in self.questions if q.get("category")})

    def get_by_ids(self, ids: List[int]) -> List[dict]:
        id_set = set(ids)
        return [q for q in self.questions if q["id"] in id_set]
