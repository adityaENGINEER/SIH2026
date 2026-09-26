import os
import json
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, List
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Deliverable

class DeliverableRepository(ABC):
    @abstractmethod
    def create_deliverable(self, deliverable_id: str, project_id: str, title: str, type: str) -> dict:
        pass

    @abstractmethod
    def get_deliverables(self, project_id: str) -> list:
        pass

    @abstractmethod
    def get_deliverable(self, project_id: str, deliverable_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def update_deliverable(self, project_id: str, deliverable_id: str, updates: dict) -> Optional[dict]:
        pass

class JsonDeliverableRepository(DeliverableRepository):
    def __init__(self):
        self.outputs_dir = os.path.join(settings.storage_root, "outputs")
        os.makedirs(self.outputs_dir, exist_ok=True)

    def _get_deliverable_path(self, project_id: str, deliverable_id: str) -> str:
        return os.path.join(self.outputs_dir, project_id, deliverable_id, "metadata.json")

    def create_deliverable(self, deliverable_id: str, project_id: str, title: str, type: str) -> dict:
        d_dir = os.path.join(self.outputs_dir, project_id, deliverable_id)
        os.makedirs(d_dir, exist_ok=True)
        now = datetime.utcnow().isoformat() + "Z"
        
        meta = {
            "deliverable_id": deliverable_id,
            "project_id": project_id,
            "title": title,
            "type": type,
            "status": "pending",
            "file_path": None,
            "created_at": now
        }
        
        with open(self._get_deliverable_path(project_id, deliverable_id), "w") as f:
            json.dump(meta, f, indent=2)
            
        return meta

    def get_deliverables(self, project_id: str) -> list:
        p_dir = os.path.join(self.outputs_dir, project_id)
        if not os.path.exists(p_dir):
            return []
            
        results = []
        for d in os.listdir(p_dir):
            meta_path = os.path.join(p_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        results.append(json.load(f))
                except:
                    pass
        return results

    def get_deliverable(self, project_id: str, deliverable_id: str) -> Optional[dict]:
        path = self._get_deliverable_path(project_id, deliverable_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def update_deliverable(self, project_id: str, deliverable_id: str, updates: dict) -> Optional[dict]:
        path = self._get_deliverable_path(project_id, deliverable_id)
        if not os.path.exists(path):
            return None
            
        with open(path, "r") as f:
            data = json.load(f)
            
        for k, v in updates.items():
            data[k] = v
            
        temp_path = path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
        return data

class PostgresDeliverableRepository(DeliverableRepository):
    def create_deliverable(self, deliverable_id: str, project_id: str, title: str, type: str) -> dict:
        now = datetime.utcnow().isoformat() + "Z"
        db = SessionLocal()
        try:
            db_deliv = Deliverable(
                deliverable_id=deliverable_id,
                project_id=project_id,
                title=title,
                type=type,
                status="pending",
                file_path=None,
                created_at=now
            )
            db.add(db_deliv)
            db.commit()
            db.refresh(db_deliv)
            return self._to_dict(db_deliv)
        finally:
            db.close()

    def get_deliverables(self, project_id: str) -> list:
        db = SessionLocal()
        try:
            delivs = db.query(Deliverable).filter(Deliverable.project_id == project_id).all()
            return [self._to_dict(d) for d in delivs]
        finally:
            db.close()

    def get_deliverable(self, project_id: str, deliverable_id: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            d = db.query(Deliverable).filter(Deliverable.deliverable_id == deliverable_id, Deliverable.project_id == project_id).first()
            return self._to_dict(d) if d else None
        finally:
            db.close()

    def update_deliverable(self, project_id: str, deliverable_id: str, updates: dict) -> Optional[dict]:
        db = SessionLocal()
        try:
            d = db.query(Deliverable).filter(Deliverable.deliverable_id == deliverable_id, Deliverable.project_id == project_id).first()
            if not d: return None
            
            for k, v in updates.items():
                if hasattr(d, k):
                    setattr(d, k, v)
                    
            db.commit()
            db.refresh(d)
            return self._to_dict(d)
        finally:
            db.close()

    def _to_dict(self, model: Deliverable) -> dict:
        return {
            "deliverable_id": model.deliverable_id,
            "project_id": model.project_id,
            "title": model.title,
            "type": model.type,
            "status": model.status,
            "file_path": model.file_path,
            "created_at": model.created_at
        }

def get_deliverable_repository() -> DeliverableRepository:
    if settings.persistence_backend == "postgres":
        return PostgresDeliverableRepository()
    return JsonDeliverableRepository()
