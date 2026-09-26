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
        self.reviews_dir = settings.reviews_dir
        os.makedirs(self.reviews_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _project_dir(self, project_id: str) -> str:
        p = os.path.join(self.reviews_dir, project_id)
        # Path-traversal guard
        if not os.path.abspath(p).startswith(os.path.abspath(self.reviews_dir)):
            raise ValueError("Invalid project_id path.")
        return p

    def _approval_path(self, project_id: str, approval_id: str) -> str:
        d = self._project_dir(project_id)
        p = os.path.join(d, f"{approval_id}.json")
        if not os.path.abspath(p).startswith(os.path.abspath(self.reviews_dir)):
            raise ValueError("Invalid approval_id path.")
        return p

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _save(self, data: dict, project_id: str, approval_id: str):
        d = self._project_dir(project_id)
        os.makedirs(d, exist_ok=True)
        path = self._approval_path(project_id, approval_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self, project_id: str, approval_id: str) -> Optional[dict]:
        path = self._approval_path(project_id, approval_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

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
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        now = self._now()
        data = {
            "approval_id": approval_id,
            "project_id": project_id,
            "conversation_id": conversation_id,
            "task_id": task_id,
            "agent_run_id": agent_run_id,
            "deliverable_id": deliverable_id,
            "title": title,
            "status": "DRAFT",
            "created_at": now,
            "updated_at": now,
            "submitted_at": None,
            "reviewed_at": None,
            "approver_name": None,
            "employee_id": None,
            "review_comment": None,
            "rejection_reason": None,
            "approval_reason": None,
            "signature_status": "unsigned",
            "source_document_ids": source_document_ids or [],
            "output_document_ids": output_document_ids or [],
        }
        self._save(data, project_id, approval_id)
        logger.info(f"Approval created: {approval_id} for project {project_id}")
        return data

    def get_approval(self, project_id: str, approval_id: str) -> Optional[dict]:
        data = self._load(project_id, approval_id)
        if data is None:
            return None
        # Enforce project isolation
        if data.get("project_id") != project_id:
            return None
        return data

    def list_approvals(self, project_id: str) -> List[dict]:
        d = self._project_dir(project_id)
        if not os.path.exists(d):
            return []
        results = []
        for fname in os.listdir(d):
            if fname.endswith(".json"):
                approval_id = fname[:-5]
                a = self._load(project_id, approval_id)
                if a and a.get("project_id") == project_id:
                    results.append(a)
        return results

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
        data["status"] = "PENDING_HUMAN_SIGNOFF"
        data["submitted_at"] = now
        data["updated_at"] = now
        self._save(data, project_id, approval_id)
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
        data["status"] = "APPROVED"
        data["reviewed_at"] = now
        data["updated_at"] = now
        data["approver_name"] = approver_name
        data["employee_id"] = employee_id
        data["approval_reason"] = reason
        data["review_comment"] = comment
        data["signature_status"] = "signed"
        self._save(data, project_id, approval_id)
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
        data["status"] = "REJECTED"
        data["reviewed_at"] = now
        data["updated_at"] = now
        data["approver_name"] = approver_name
        data["employee_id"] = employee_id
        data["rejection_reason"] = reason
        data["review_comment"] = comment
        self._save(data, project_id, approval_id)
        logger.info(f"Approval {approval_id} REJECTED by {approver_name} (ID: {employee_id}).")
        return data


approval_service = ApprovalService()
