"""
Approval service — local filesystem persistence only.
Storage: D:\\SovereignAI\\storage\\reviews\\{project_id}\\{approval_id}.json

Lifecycle:
  DRAFT → PENDING_HUMAN_SIGNOFF → APPROVED / REJECTED

AI/Tuffy NEVER sets status to APPROVED. Only explicit human action may do so.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict

from app.core.config import settings
from app.repositories.approval_repository import get_approval_repository

logger = logging.getLogger(__name__)

VALID_STATUSES = {"DRAFT", "PENDING_HUMAN_SIGNOFF", "APPROVED", "REJECTED"}

# Transitions allowed by the API (source → set of targets)
ALLOWED_TRANSITIONS = {
    "DRAFT": {"PENDING_HUMAN_SIGNOFF"},
    "PENDING_HUMAN_SIGNOFF": {"APPROVED", "REJECTED"},
    "APPROVED": set(),   # terminal
    "REJECTED": set(),   # terminal
}


class ApprovalService:
    def __init__(self):
        self.repo = get_approval_repository()

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def create_approval(
        self,
        project_id: str,
        title: str,
        conversation_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        deliverable_id: Optional[str] = None,
        source_document_ids: Optional[List[str]] = None,
        output_document_ids: Optional[List[str]] = None,
    ) -> dict:
        data = self.repo.create_approval(
            project_id=project_id,
            title=title,
            conversation_id=conversation_id,
            task_id=task_id,
            agent_run_id=agent_run_id,
            deliverable_id=deliverable_id,
            source_document_ids=source_document_ids,
            output_document_ids=output_document_ids
        )
        logger.info(f"Approval created: {data['approval_id']} for project {project_id}")
        return data

    def get_approval(self, project_id: str, approval_id: str) -> Optional[dict]:
        return self.repo.get_approval(project_id, approval_id)

    def list_approvals(self, project_id: str) -> List[dict]:
        return self.repo.list_approvals(project_id)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def submit_for_review(self, project_id: str, approval_id: str) -> dict:
        """DRAFT → PENDING_HUMAN_SIGNOFF"""
        data = self.get_approval(project_id, approval_id)
        if data is None:
            return {"error": {"code": "APPROVAL_NOT_FOUND", "message": "Approval not found."}}
        
        current = data["status"]
        if "PENDING_HUMAN_SIGNOFF" not in ALLOWED_TRANSITIONS.get(current, set()):
            return {
                "error": {
                    "code": "INVALID_APPROVAL_STATE",
                    "message": f"Cannot submit for review from status '{current}'. Only DRAFT approvals can be submitted."
                }
            }
        
        now = self._now()
        updates = {
            "status": "PENDING_HUMAN_SIGNOFF",
            "submitted_at": now,
            "updated_at": now
        }
        data = self.repo.update_approval(project_id, approval_id, updates)
        logger.info(f"Approval {approval_id} submitted for review.")
        return data

    def approve(
        self,
        project_id: str,
        approval_id: str,
        approver_name: str,
        employee_id: str,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> dict:
        """PENDING_HUMAN_SIGNOFF → APPROVED (human-only action)"""
        data = self.get_approval(project_id, approval_id)
        if data is None:
            return {"error": {"code": "APPROVAL_NOT_FOUND", "message": "Approval not found."}}
        
        current = data["status"]
        if "APPROVED" not in ALLOWED_TRANSITIONS.get(current, set()):
            return {
                "error": {
                    "code": "INVALID_APPROVAL_STATE",
                    "message": f"Cannot approve from status '{current}'. Approval must be PENDING_HUMAN_SIGNOFF."
                }
            }
        
        now = self._now()
        updates = {
            "status": "APPROVED",
            "reviewed_at": now,
            "updated_at": now,
            "approver_name": approver_name,
            "employee_id": employee_id,
            "approval_reason": reason,
            "review_comment": comment,
            "signature_status": "signed"
        }
        data = self.repo.update_approval(project_id, approval_id, updates)
        logger.info(f"Approval {approval_id} APPROVED by {approver_name} (ID: {employee_id}).")
        return data

    def reject(
        self,
        project_id: str,
        approval_id: str,
        approver_name: str,
        employee_id: str,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> dict:
        """PENDING_HUMAN_SIGNOFF → REJECTED (human-only action)"""
        data = self.get_approval(project_id, approval_id)
        if data is None:
            return {"error": {"code": "APPROVAL_NOT_FOUND", "message": "Approval not found."}}
        
        current = data["status"]
        if "REJECTED" not in ALLOWED_TRANSITIONS.get(current, set()):
            return {
                "error": {
                    "code": "INVALID_APPROVAL_STATE",
                    "message": f"Cannot reject from status '{current}'. Approval must be PENDING_HUMAN_SIGNOFF."
                }
            }
        
        now = self._now()
        updates = {
            "status": "REJECTED",
            "reviewed_at": now,
            "updated_at": now,
            "approver_name": approver_name,
            "employee_id": employee_id,
            "rejection_reason": reason,
            "review_comment": comment
        }
        data = self.repo.update_approval(project_id, approval_id, updates)
        logger.info(f"Approval {approval_id} REJECTED by {approver_name} (ID: {employee_id}).")
        return data


approval_service = ApprovalService()
