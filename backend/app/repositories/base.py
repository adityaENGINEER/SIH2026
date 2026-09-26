from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class ProjectRepository(ABC):
    @abstractmethod
    def create_project(self, name: str, description: str = "", project_type: str = "general") -> dict:
        pass

    @abstractmethod
    def get_projects(self) -> List[dict]:
        pass

    @abstractmethod
    def get_project(self, project_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def update_project(self, project_id: str, updates: dict) -> Optional[dict]:
        pass

    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        pass
