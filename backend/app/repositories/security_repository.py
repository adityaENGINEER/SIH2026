import os
import json
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import SecurityEvent

class SecurityRepository(ABC):
    @abstractmethod
    def log_event(self, event_type: str, source: str, destination: str, allowed: bool, 
                  reason: str = None, project_id: str = None, task_id: str = None, 
                  agent_run_id: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_events(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

class JsonSecurityRepository(SecurityRepository):
    def __init__(self):
        self.security_dir = os.path.join(settings.storage_root, "security")
        os.makedirs(self.security_dir, exist_ok=True)
        self.events_file = os.path.join(self.security_dir, "events.json")
        if not os.path.exists(self.events_file):
            with open(self.events_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def log_event(self, event_type: str, source: str, destination: str, allowed: bool, 
                  reason: str = None, project_id: str = None, task_id: str = None, 
                  agent_run_id: str = None) -> Dict[str, Any]:
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
                events.insert(0, event)
                f.seek(0)
                json.dump(events, f, indent=2)
                f.truncate()
        except Exception:
            pass
        return event

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

class PostgresSecurityRepository(SecurityRepository):
    def log_event(self, event_type: str, source: str, destination: str, allowed: bool, 
                  reason: str = None, project_id: str = None, task_id: str = None, 
                  agent_run_id: str = None) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        details = {
            "source": source,
            "destination": destination,
            "allowed": allowed,
            "blocked": not allowed,
            "reason": reason,
            "project_id": project_id,
            "task_id": task_id,
            "agent_run_id": agent_run_id
        }
        
        db = SessionLocal()
        try:
            db_event = SecurityEvent(
                event_type=event_type,
                timestamp=now,
                details=details
            )
            db.add(db_event)
            db.commit()
            db.refresh(db_event)
            return self._to_dict(db_event)
        finally:
            db.close()

    def get_events(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(SecurityEvent).order_by(SecurityEvent.id.desc())
            if project_id:
                # Naive filter since it's JSON in PG
                events = query.all()
                return [self._to_dict(e) for e in events if e.details.get("project_id") == project_id]
            return [self._to_dict(e) for e in query.all()]
        finally:
            db.close()

    def _to_dict(self, model: SecurityEvent) -> dict:
        d = model.details.copy()
        d["event_id"] = f"evt_db_{model.id}"
        d["timestamp"] = model.timestamp
        d["event_type"] = model.event_type
        return d

def get_security_repository() -> SecurityRepository:
    if settings.persistence_backend == "postgres":
        return PostgresSecurityRepository()
    return JsonSecurityRepository()
