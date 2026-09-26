import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.repositories.security_repository import get_security_repository

class SecurityService:
    def __init__(self):
        self.repo = get_security_repository()

    def log_event(
        self,
        event_type: str,
        source: str,
        destination: str,
        allowed: bool,
        reason: str = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.repo.log_event(
            event_type=event_type,
            source=source,
            destination=destination,
            allowed=allowed,
            reason=reason,
            project_id=project_id,
            task_id=task_id,
            agent_run_id=agent_run_id
        )

    @staticmethod
    def is_local_url(url: str) -> bool:
        from urllib.parse import urlparse
        return (urlparse(url).hostname or "").lower() in {"localhost", "127.0.0.1", "::1"}

    def record_model_call(self, operation: str, model: str, destination_url: str) -> bool:
        """Logs a local model call (or blocks a non-local one). Returns True if the call may proceed."""
        from app.core.request_context import current_project_id, current_task_id
        allowed = self.is_local_url(destination_url)
        self.log_event(
            event_type="model_call" if allowed else "network_attempt",
            source=f"{operation}:{model}",
            destination=destination_url,
            allowed=allowed,
            reason="local Ollama inference" if allowed else "non-local model endpoint blocked by local-only policy",
            project_id=current_project_id.get(),
            task_id=current_task_id.get(),
            agent_run_id=current_task_id.get(),
        )
        return allowed

    def get_events(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.repo.get_events(project_id)

    def get_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        events = self.get_events(project_id)
        
        total_evaluations = sum(1 for e in events if e.get("event_type") == "model_call")
        outbound_calls = sum(1 for e in events if e.get("event_type") == "network_attempt")
        blocked_calls = sum(1 for e in events if e.get("blocked"))
        local_calls = sum(1 for e in events if e.get("event_type") in ["model_call", "tool_execution", "file_operation"])
        
        return {
            "total_evaluations": total_evaluations,
            "outbound_calls": outbound_calls,
            "blocked_calls": blocked_calls,
            "local_calls": local_calls
        }

security_service = SecurityService()
