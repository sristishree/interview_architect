from typing import Dict, List, Optional
from pydantic import BaseModel, field_validator

from .enums import Difficulty, QuestionType

class GeneratedQuestion(BaseModel):
    """A question produced by an LLM tool before being saved to the knowledge base.
    Identical to Question but without id — the store assigns that on save."""
    topic: str
    difficulty: Difficulty
    category: str
    tags: List[str]
    question: str
    follow_up: Optional[str] = None
    question_type: QuestionType = QuestionType.theory

    @field_validator('difficulty', mode='before')
    @classmethod
    def coerce_difficulty(cls, v):
        try:
            return Difficulty(v)
        except ValueError:
            return Difficulty.medium

    @field_validator('question_type', mode='before')
    @classmethod
    def coerce_question_type(cls, v):
        try:
            return QuestionType(v)
        except ValueError:
            return QuestionType.theory


class GeneratedQuestionList(BaseModel):
    """Wrapper used as the structured output schema for LLM tool calls."""
    questions: List[GeneratedQuestion]


class Question(BaseModel):
    id: int
    topic: str
    difficulty: Difficulty
    category: str
    tags: List[str]
    question: str
    follow_up: Optional[str] = None
    question_type: QuestionType = QuestionType.theory


class InterviewSection(BaseModel):
    name: str
    questions: List[Question]


class InterviewSet(BaseModel):
    candidate_name: str
    total_questions: int
    estimated_duration_minutes: int
    resolved_difficulty: str
    sections: List[InterviewSection]
    curator_notes: str
