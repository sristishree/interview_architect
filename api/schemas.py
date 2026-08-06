from typing import Optional
from pydantic import BaseModel


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
