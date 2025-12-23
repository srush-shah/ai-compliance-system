from typing import Dict, Optional

from pydantic import BaseModel


class WorkflowStepResult(BaseModel):
    step: str
    status: str
    data: Optional[Dict] = None
    error: Optional[str] = None

class WorkflowResult(BaseModel):
    status: str
    raw_id: int
    processed_id: Optional[int] = None
    report_id: Optional[int] = None
    steps: Dict[str, WorkflowStepResult]