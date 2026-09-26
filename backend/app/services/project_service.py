import os
import json
import uuid
import shutil
from datetime import datetime
from app.core.config import settings

class ProjectService:
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
        
        # Write atomic
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

project_service = ProjectService()
