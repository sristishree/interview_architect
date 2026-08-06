from typing import Dict, List
from pydantic import BaseModel, Field

from .enums import Difficulty, QuestionType, Source

class TopicPlan(BaseModel):
    topic: str = Field(description="The specific topic or project to cover")
    source: Source
    n_questions: int = Field(description="How many questions to retrieve for this topic")
    difficulty: Difficulty
    question_types: Dict[QuestionType, int] = Field(
        description="Breakdown by type: {implementation: 2, design: 1, theory: 1}"
    )


class InterviewPlan(BaseModel):
    """
    Strategic allocation produced by the Planner agent.
    This is the most important reasoning artifact — inspect it in LangSmith.
    """
    total_questions: int
    resolved_difficulty: Difficulty = Field(description="Final difficulty after applying override if any")
    reasoning: str = Field(description="Why these topics and allocations were chosen")
    topic_plans: List[TopicPlan]
