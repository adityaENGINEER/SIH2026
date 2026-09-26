from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    project_type: Optional[str] = "general"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str
    project_type: str
    status: str
    created_at: str
    updated_at: str
