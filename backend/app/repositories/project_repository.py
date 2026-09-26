import os
import json
import uuid
import shutil
from datetime import datetime
from app.core.config import settings
from app.repositories.base import ProjectRepository
from app.db.database import SessionLocal
from app.db.models import Project

class JsonProjectRepository(ProjectRepository):
    def __init__(self):
        os.makedirs(settings.projects_dir, exist_ok=True)

    def _get_project_path(self, project_id: str) -> str:
        return os.path.join(settings.projects_dir, project_id, "project.json")

    def create_project(self, name: str, description: str = "", project_type: str = "general") -> dict:
        project_id = f"proj_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        project_dir = os.path.join(settings.projects_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        now = datetime.utcnow().isoformat() + "Z"
        project_data = {
            "project_id": project_id,
            "name": name,
            "description": description,
            "project_type": project_type,
            "status": "active",
            "created_at": now,
            "updated_at": now
        }
        
        with open(os.path.join(project_dir, "project.json"), "w") as f:
            json.dump(project_data, f, indent=2)
            
        return project_data

    def get_projects(self) -> list:
        projects = []
        if not os.path.exists(settings.projects_dir):
            return projects
            
        for d in os.listdir(settings.projects_dir):
            p_path = self._get_project_path(d)
            if os.path.exists(p_path):
                try:
                    with open(p_path, "r") as f:
                        projects.append(json.load(f))
                except:
                    pass
        return projects

    def get_project(self, project_id: str) -> dict:
        p_path = self._get_project_path(project_id)
        if not os.path.exists(p_path):
            return None
        with open(p_path, "r") as f:
            return json.load(f)

    def update_project(self, project_id: str, updates: dict) -> dict:
        p_path = self._get_project_path(project_id)
        if not os.path.exists(p_path):
            return None
            
        with open(p_path, "r") as f:
            data = json.load(f)
            
        for k, v in updates.items():
            if v is not None:
                data[k] = v
                
        data["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        temp_path = p_path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, p_path)
        
        return data

    def delete_project(self, project_id: str) -> bool:
        project_dir = os.path.join(settings.projects_dir, project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir, ignore_errors=True)
            return True
        return False

class PostgresProjectRepository(ProjectRepository):
    def create_project(self, name: str, description: str = "", project_type: str = "general") -> dict:
        project_id = f"proj_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        
        db = SessionLocal()
        try:
            db_project = Project(
                project_id=project_id,
                name=name,
                description=description,
                project_type=project_type,
                status="active",
                created_at=now,
                updated_at=now
            )
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            return self._to_dict(db_project)
        finally:
            db.close()

    def get_projects(self) -> list:
        db = SessionLocal()
        try:
            projects = db.query(Project).all()
            return [self._to_dict(p) for p in projects]
        finally:
            db.close()

    def get_project(self, project_id: str) -> dict:
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.project_id == project_id).first()
            return self._to_dict(p) if p else None
        finally:
            db.close()

    def update_project(self, project_id: str, updates: dict) -> dict:
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.project_id == project_id).first()
            if not p: return None
            for k, v in updates.items():
                if v is not None and hasattr(p, k):
                    setattr(p, k, v)
            p.updated_at = datetime.utcnow().isoformat() + "Z"
            db.commit()
            db.refresh(p)
            return self._to_dict(p)
        finally:
            db.close()

    def delete_project(self, project_id: str) -> bool:
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.project_id == project_id).first()
            if not p: return False
            db.delete(p)
            db.commit()
            return True
        finally:
            db.close()

    def _to_dict(self, model: Project) -> dict:
        return {
            "project_id": model.project_id,
            "name": model.name,
            "description": model.description,
            "project_type": model.project_type,
            "status": model.status,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }

def get_project_repository() -> ProjectRepository:
    if settings.persistence_backend == "postgres":
        return PostgresProjectRepository()
    return JsonProjectRepository()
