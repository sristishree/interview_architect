"""
LLM normalization step for the ingestion pipeline.

Takes raw Q&A pairs ({"raw_question", "raw_answer"}) from any adapter and maps
each into the full question schema. Processes in batches to reduce API calls.

Difficulty and question_type are inferred per-question by the LLM — not bulk-defaulted.
Category can be a new value not in the existing 8 if the question genuinely doesn't fit.
"""
import json
import logging
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.config import get_structured_llm
from app.models.enums import Difficulty, QuestionType

logger = logging.getLogger(__name__)

BATCH_SIZE = 8

EXISTING_CATEGORIES = ["ML", "Python", "LLM", "General", "SQL", "SystemDesign", "Leadership", "Cloud"]


class NormalizedQuestion(BaseModel):
    topic: str               # specific topic, e.g. "Gradient Boosting" not "ML"
    category: str            # from EXISTING_CATEGORIES or a new value if nothing fits
    tags: List[str]          # 3–5 specific technical keywords
    question: str            # cleaned/rephrased question text
    follow_up: Optional[str] = None
    question_type: QuestionType
    difficulty: Difficulty
    answer: Optional[str] = None  # verbatim from source; null if not provided

    @field_validator("difficulty", mode="before")
    @classmethod
    def coerce_difficulty(cls, v):
        try:
            return Difficulty(v)
        except ValueError:
            return Difficulty.medium

    @field_validator("question_type", mode="before")
    @classmethod
    def coerce_question_type(cls, v):
        try:
            return QuestionType(v)
        except ValueError:
            return QuestionType.theory


class NormalizedBatch(BaseModel):
    questions: List[NormalizedQuestion]


_SYSTEM = f"""You normalize raw interview Q&A pairs into a structured schema.

For EACH pair in the input list:
1. topic — specific (e.g. "XGBoost Feature Importance", not "ML")
2. category — pick from {EXISTING_CATEGORIES} if it fits; otherwise invent a concise new one
3. tags — 3–5 specific technical keywords (not generic like "machine learning")
4. question — clean, grammatically correct question text; rephrase only if needed for clarity
5. follow_up — a sharper follow-up question that probes deeper; generate one if not provided
6. question_type — infer from content:
   - implementation: asks HOW to build/code/implement something
   - theory: asks about concepts, definitions, how things work internally
   - design: asks to design a system, architecture, or approach
   - optimization: asks how to improve performance, efficiency, or scale
   - behavioral: asks about past experience, decisions, team dynamics
   - case_study: presents a scenario requiring analysis and recommendation
7. difficulty — infer from technical depth:
   - Easy: basic concept/syntax, entry-level
   - Medium: requires genuine understanding, moderate experience
   - Hard: requires deep expertise, trade-off reasoning, or system-level thinking
8. answer — copy verbatim from raw_answer if provided; set null if raw_answer is null

Return exactly one normalized question per input pair, in the same order."""


def normalize_batch(raw_pairs: List[dict], source_id: str) -> List[dict]:
    """
    Normalize a list of raw Q&A dicts into the question schema.
    Returns list of dicts ready for staging (no id assigned yet).
    """
    llm = get_structured_llm(NormalizedBatch, fast=True)
    results = []

    for i in range(0, len(raw_pairs), BATCH_SIZE):
        chunk = raw_pairs[i : i + BATCH_SIZE]
        prompt = (
            f"Normalize these {len(chunk)} Q&A pairs:\n\n"
            + json.dumps(chunk, indent=2)
        )
        try:
            batch = llm.invoke([("system", _SYSTEM), ("human", prompt)])
        except Exception as e:
            logger.error("Normalization failed for batch %d–%d: %s", i, i + len(chunk), e)
            continue

        if len(batch.questions) != len(chunk):
            logger.warning(
                "Batch %d–%d: sent %d, got %d back — using what we got",
                i, i + len(chunk), len(chunk), len(batch.questions),
            )

        for nq in batch.questions:
            results.append({
                "topic": nq.topic,
                "category": nq.category,
                "tags": nq.tags,
                "question": nq.question,
                "follow_up": nq.follow_up,
                "question_type": nq.question_type.value,
                "difficulty": nq.difficulty.value,
                "answer": nq.answer,
                "source": source_id,
            })

        logger.info(
            "Normalized batch %d–%d (%d/%d done)",
            i, i + len(chunk), min(i + BATCH_SIZE, len(raw_pairs)), len(raw_pairs),
        )

    return results
