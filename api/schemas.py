from typing import Optional
from pydantic import BaseModel, Field

from app.models.focus import FocusConfig


class RunCreatedResponse(BaseModel):
    thread_id: str
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    thread_id: str
    run_id: str
    status: str  # "pending" | "running" | "success" | "error"
    result: Optional[dict] = None
    error: Optional[str] = None


class GenerateRequest(BaseModel):
    """
    Optional body fields for POST /interview.
    The resume file is still uploaded as multipart/form-data.
    focus_config and question_count_override are sent as JSON-encoded form fields.
    """
    focus_config: Optional[FocusConfig] = None
    question_count_override: Optional[int] = Field(default=None, ge=5, le=30)
