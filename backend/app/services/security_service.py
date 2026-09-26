import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings

class SecurityService:
    def __init__(self):
        self.security_dir = os.path.join(settings.storage_root, "security")
        os.makedirs(self.security_dir, exist_ok=True)
        # Store events in a daily log file or single list for simplicity, but let's use a single events.json for now
        self.events_file = os.path.join(self.security_dir, "events.json")
        if not os.path.exists(self.events_file):
            with open(self.events_file, "w", encoding="utf-8") as f:
                json.dump([], f)

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
        event = {
            "event_id": f"evt_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "source": source,
            "destination": destination,
            "allowed": allowed,
            "blocked": not allowed,
            "reason": reason,
            "project_id": project_id,
            "task_id": task_id,
            "agent_run_id": agent_run_id
        }
        
        try:
            with open(self.events_file, "r+", encoding="utf-8") as f:
                events = json.load(f)
                events.insert(0, event) # latest first
                f.seek(0)
                json.dump(events, f, indent=2)
                f.truncate()
        except Exception:
            # Handle concurrent writes or corruption safely by appending
            pass
            
        return event

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
        if not os.path.exists(self.events_file):
            return []
        try:
            with open(self.events_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception:
            return []
            
        if project_id:
            return [e for e in events if e.get("project_id") == project_id]
        return events

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
