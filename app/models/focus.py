from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import QuestionType


class InterviewMode(str, Enum):
    FULL = "full"
    FOCUSED = "focused"


class ResumeSection(str, Enum):
    WORK_EXPERIENCE = "work_experience"
    PROJECTS = "projects"
    SKILLS = "skills"


class FocusConfig(BaseModel):
    section: ResumeSection
    question_types: Optional[List[QuestionType]] = None  # None = all types allowed
    modifier: Optional[str] = None                        # soft prompt steer only
    question_count: Optional[int] = Field(default=None, ge=5, le=30)  # None = let planner decide
