import os
import json
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, List
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Approval

class ApprovalRepository(ABC):
    @abstractmethod
    def create_approval(self, project_id: str, title: str, conversation_id: str = None, 
                        task_id: str = None, agent_run_id: str = None, deliverable_id: str = None, 
                        source_document_ids: List[str] = None, output_document_ids: List[str] = None) -> dict:
        pass

    @abstractmethod
    def get_approval(self, project_id: str, approval_id: str) -> Optional[dict]:
        pass
        
    @abstractmethod
    def list_approvals(self, project_id: str) -> List[dict]:
        pass

    @abstractmethod
    def update_approval(self, project_id: str, approval_id: str, updates: dict) -> Optional[dict]:
        pass

class JsonApprovalRepository(ApprovalRepository):
    def __init__(self):
        self.reviews_dir = settings.reviews_dir
        os.makedirs(self.reviews_dir, exist_ok=True)

    def _project_dir(self, project_id: str) -> str:
        p = os.path.join(self.reviews_dir, project_id)
        if not os.path.abspath(p).startswith(os.path.abspath(self.reviews_dir)):
            raise ValueError("Invalid project_id path.")
        return p

    def _approval_path(self, project_id: str, approval_id: str) -> str:
        d = self._project_dir(project_id)
        return os.path.join(d, f"{approval_id}.json")

    def _now(self):
        return datetime.utcnow().isoformat() + "Z"

    def create_approval(self, project_id: str, title: str, conversation_id: str = None, 
                        task_id: str = None, agent_run_id: str = None, deliverable_id: str = None, 
                        source_document_ids: List[str] = None, output_document_ids: List[str] = None) -> dict:
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
        
        d = self._project_dir(project_id)
        os.makedirs(d, exist_ok=True)
        path = self._approval_path(project_id, approval_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return data

    def get_approval(self, project_id: str, approval_id: str) -> Optional[dict]:
        path = self._approval_path(project_id, approval_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
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
                a = self.get_approval(project_id, fname[:-5])
                if a:
                    results.append(a)
        return results

    def update_approval(self, project_id: str, approval_id: str, updates: dict) -> Optional[dict]:
        path = self._approval_path(project_id, approval_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for k, v in updates.items():
            data[k] = v
            
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp, path)
        return data

class PostgresApprovalRepository(ApprovalRepository):
    def _now(self):
        return datetime.utcnow().isoformat() + "Z"

    def create_approval(self, project_id: str, title: str, conversation_id: str = None, 
                        task_id: str = None, agent_run_id: str = None, deliverable_id: str = None, 
                        source_document_ids: List[str] = None, output_document_ids: List[str] = None) -> dict:
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        now = self._now()
        db = SessionLocal()
        try:
            db_approval = Approval(
                approval_id=approval_id,
                project_id=project_id,
                conversation_id=conversation_id,
                task_id=task_id,
                agent_run_id=agent_run_id,
                deliverable_id=deliverable_id,
                title=title,
                status="DRAFT",
                created_at=now,
                updated_at=now,
                submitted_at=None,
                reviewed_at=None,
                approver_name=None,
                employee_id=None,
                review_comment=None,
                rejection_reason=None,
                approval_reason=None,
                signature_status="unsigned",
                source_document_ids=source_document_ids or [],
                output_document_ids=output_document_ids or []
            )
            db.add(db_approval)
            db.commit()
            db.refresh(db_approval)
            return self._to_dict(db_approval)
        finally:
            db.close()

    def get_approval(self, project_id: str, approval_id: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            a = db.query(Approval).filter(Approval.approval_id == approval_id, Approval.project_id == project_id).first()
            return self._to_dict(a) if a else None
        finally:
            db.close()
            
    def list_approvals(self, project_id: str) -> List[dict]:
        db = SessionLocal()
        try:
            apps = db.query(Approval).filter(Approval.project_id == project_id).all()
            return [self._to_dict(a) for a in apps]
        finally:
            db.close()

    def update_approval(self, project_id: str, approval_id: str, updates: dict) -> Optional[dict]:
        db = SessionLocal()
        try:
            a = db.query(Approval).filter(Approval.approval_id == approval_id, Approval.project_id == project_id).first()
            if not a: return None
            for k, v in updates.items():
                if hasattr(a, k):
                    setattr(a, k, v)
            db.commit()
            db.refresh(a)
            return self._to_dict(a)
        finally:
            db.close()

    def _to_dict(self, model: Approval) -> dict:
        return {
            "approval_id": model.approval_id,
            "project_id": model.project_id,
            "conversation_id": model.conversation_id,
            "task_id": model.task_id,
            "agent_run_id": model.agent_run_id,
            "deliverable_id": model.deliverable_id,
            "title": model.title,
            "status": model.status,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "submitted_at": model.submitted_at,
            "reviewed_at": model.reviewed_at,
            "approver_name": model.approver_name,
            "employee_id": model.employee_id,
            "review_comment": model.review_comment,
            "rejection_reason": model.rejection_reason,
            "approval_reason": model.approval_reason,
            "signature_status": model.signature_status,
            "source_document_ids": model.source_document_ids,
            "output_document_ids": model.output_document_ids
        }

def get_approval_repository() -> ApprovalRepository:
    if settings.persistence_backend == "postgres":
        return PostgresApprovalRepository()
    return JsonApprovalRepository()
