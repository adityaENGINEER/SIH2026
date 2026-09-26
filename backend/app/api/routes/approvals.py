"""
Approval API routes — project-scoped, strict state-machine enforcement.
All approvals are stored under D:\\SovereignAI\\storage\\reviews\\{project_id}\\
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.approvals import (
    ApprovalCreate,
    ApprovalDecisionRequest,
    ApprovalResponse,
)
from app.services.approval_service import approval_service

router = APIRouter()


def _err(data: dict):
    """Raise 400/404 from a service error dict."""
    err = data.get("error", {})
    code = err.get("code", "UNKNOWN_ERROR")
    msg = err.get("message", "An error occurred.")
    status = 404 if "NOT_FOUND" in code else 400
    raise HTTPException(status_code=status, detail={"code": code, "message": msg})


@router.post("/{project_id}/approvals", response_model=ApprovalResponse)
def create_approval(project_id: str, req: ApprovalCreate):
    result = approval_service.create_approval(
        project_id=project_id,
        title=req.title,
        conversation_id=req.conversation_id,
        task_id=req.task_id,
        agent_run_id=req.agent_run_id,
        deliverable_id=req.deliverable_id,
        source_document_ids=req.source_document_ids,
        output_document_ids=req.output_document_ids,
    )
    if "error" in result:
        _err(result)
    return result


@router.get("/{project_id}/approvals", response_model=List[ApprovalResponse])
def list_approvals(project_id: str):
    return approval_service.list_approvals(project_id)


@router.get("/{project_id}/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(project_id: str, approval_id: str):
    result = approval_service.get_approval(project_id, approval_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "APPROVAL_NOT_FOUND", "message": "Approval not found."},
        )
    return result


@router.post("/{project_id}/approvals/{approval_id}/submit")
def submit_approval(project_id: str, approval_id: str):
    result = approval_service.submit_for_review(project_id, approval_id)
    if "error" in result:
        _err(result)
    return result


@router.post("/{project_id}/approvals/{approval_id}/approve")
def approve_approval(project_id: str, approval_id: str, req: ApprovalDecisionRequest):
    result = approval_service.approve(
        project_id=project_id,
        approval_id=approval_id,
        approver_name=req.approver_name,
        employee_id=req.employee_id,
        reason=req.reason,
        comment=req.comment,
    )
    if "error" in result:
        _err(result)
    return result


@router.post("/{project_id}/approvals/{approval_id}/reject")
def reject_approval(project_id: str, approval_id: str, req: ApprovalDecisionRequest):
    result = approval_service.reject(
        project_id=project_id,
        approval_id=approval_id,
        approver_name=req.approver_name,
        employee_id=req.employee_id,
        reason=req.reason,
        comment=req.comment,
    )
    if "error" in result:
        _err(result)
    return result
