from pydantic import BaseModel
from typing import Optional


class DeliverableCreate(BaseModel):
    project_id: str
    task_id: Optional[str] = None
    approval_id: Optional[str] = None
    format: str  # DOCX, PDF, PPTX, XLSX
    title: str
    content: Optional[str] = None  # Freeform text for the deliverable body


class DeliverableResponse(BaseModel):
    deliverable_id: str
    project_id: str
    task_id: Optional[str] = None
    approval_id: Optional[str] = None
    type: str
    filename: str
    path: str
    created_at: str
    size: int
    status: str
