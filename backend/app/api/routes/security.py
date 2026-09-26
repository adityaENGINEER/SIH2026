from fastapi import APIRouter
from typing import Optional
from app.services.security_service import security_service

router = APIRouter()

@router.get("/summary")
def get_security_summary(project_id: Optional[str] = None):
    return security_service.get_summary(project_id)

@router.get("/events")
def get_security_events(limit: int = 200):
    # System-level events only; project events are served by /api/projects/{project_id}/security/events.
    system_events = [e for e in security_service.get_events() if not e.get("project_id")]
    return system_events[:max(1, min(limit, 1000))]
