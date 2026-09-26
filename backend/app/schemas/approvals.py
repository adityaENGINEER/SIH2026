from pydantic import BaseModel
from typing import Optional, List


class ApprovalCreate(BaseModel):
    title: str
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    deliverable_id: Optional[str] = None
    source_document_ids: Optional[List[str]] = []
    output_document_ids: Optional[List[str]] = []


class ApprovalSubmitRequest(BaseModel):
    """Submits an approval for human review (DRAFT → PENDING_HUMAN_SIGNOFF)."""
    pass  # No payload needed; the action itself is the transition


class ApprovalDecisionRequest(BaseModel):
    """Human approves or rejects a PENDING_HUMAN_SIGNOFF approval."""
    approver_name: str
    employee_id: str
    comment: Optional[str] = None
    reason: Optional[str] = None  # approval_reason or rejection_reason


class ApprovalResponse(BaseModel):
    approval_id: str
    project_id: str
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    deliverable_id: Optional[str] = None
    title: str
    status: str
    created_at: str
    updated_at: str
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    approver_name: Optional[str] = None
    employee_id: Optional[str] = None
    review_comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    approval_reason: Optional[str] = None
    signature_status: str = "unsigned"
    source_document_ids: List[str] = []
    output_document_ids: List[str] = []
