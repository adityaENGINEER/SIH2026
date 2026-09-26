import os
import re
import json
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Conversation, Message

SAFE_ID = re.compile(r"^[A-Za-z0-9_\-]+$")
DEFAULT_TITLE = "New Conversation"

class ChatRepository(ABC):
    @abstractmethod
    def create_conversation(self, project_id: str, title: str = "New Conversation") -> dict:
        pass

    @abstractmethod
    def get_conversations(self, project_id: str) -> list:
        pass

    @abstractmethod
    def get_conversation_response(self, project_id: str, conversation_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def delete_conversation(self, project_id: str, conversation_id: str) -> bool:
        pass

    @abstractmethod
    def update_task_message(self, project_id: str, conversation_id: str, task_id: str, status: str) -> None:
        pass

    @abstractmethod
    def add_message(self, project_id: str, conversation_id: str, role: str, content: str, 
                    execution_mode: str = None, task_id: str = None, status: str = None,
                    routing: dict = None, error: dict = None) -> dict:
        pass

    @abstractmethod
    def get_project_chat_history(self, project_id: str, date: str = None) -> list:
        pass

class JsonChatRepository(ChatRepository):
    def _get_project_conversations_dir(self, project_id: str) -> str:
        if not SAFE_ID.match(project_id or ""):
            raise ValueError("Invalid project_id")
        return os.path.join(settings.projects_dir, project_id, "conversations")

    def _get_conversation_path(self, project_id: str, conversation_id: str) -> str:
        if not SAFE_ID.match(conversation_id or ""):
            raise ValueError("Invalid conversation_id")
        return os.path.join(self._get_project_conversations_dir(project_id), f"{conversation_id}.json")

    def create_conversation(self, project_id: str, title: str = "New Conversation") -> dict:
        conv_dir = self._get_project_conversations_dir(project_id)
        os.makedirs(conv_dir, exist_ok=True)
        
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"
        
        conv_data = {
            "conversation_id": conversation_id,
            "project_id": project_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": []
        }
        
        with open(self._get_conversation_path(project_id, conversation_id), "w") as f:
            json.dump(conv_data, f, indent=2)
            
        return self._format_conversation_response(conv_data)

    def get_conversations(self, project_id: str) -> list:
        conv_dir = self._get_project_conversations_dir(project_id)
        if not os.path.exists(conv_dir):
            return []
            
        conversations = []
        for file in os.listdir(conv_dir):
            if file.endswith(".json"):
                with open(os.path.join(conv_dir, file), "r") as f:
                    try:
                        data = json.load(f)
                        conversations.append(self._format_conversation_response(data))
                    except:
                        pass
        return conversations

    def get_conversation(self, project_id: str, conversation_id: str) -> dict:
        path = self._get_conversation_path(project_id, conversation_id)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
            
    def get_conversation_response(self, project_id: str, conversation_id: str) -> dict:
        data = self.get_conversation(project_id, conversation_id)
        if not data: return None
        return self._format_conversation_response(data)

    def delete_conversation(self, project_id: str, conversation_id: str) -> bool:
        path = self._get_conversation_path(project_id, conversation_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def update_task_message(self, project_id: str, conversation_id: str, task_id: str, status: str) -> None:
        path = self._get_conversation_path(project_id, conversation_id)
        if not os.path.exists(path):
            return
        with open(path, "r") as f:
            data = json.load(f)
        for m in data.get("messages", []):
            if m.get("task_id") == task_id:
                m["status"] = status
        temp_path = path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)

    def add_message(self, project_id: str, conversation_id: str, role: str, content: str, 
                    execution_mode: str = None, task_id: str = None, status: str = None,
                    routing: dict = None, error: dict = None) -> dict:
        path = self._get_conversation_path(project_id, conversation_id)
        if not os.path.exists(path):
            return None
            
        with open(path, "r") as f:
            data = json.load(f)
            
        now = datetime.utcnow().isoformat() + "Z"
        msg = {
            "message_id": f"msg_{uuid.uuid4().hex[:12]}",
            "conversation_id": conversation_id,
            "project_id": project_id,
            "role": role,
            "content": content,
            "created_at": now
        }
        if execution_mode: msg["execution_mode"] = execution_mode
        if task_id: msg["task_id"] = task_id
        if status: msg["status"] = status
        if routing: msg["routing"] = routing
        if error: msg["error"] = error
        
        data["messages"].append(msg)
        if role == "user" and data.get("title") in (None, "", DEFAULT_TITLE):
            data["title"] = content.strip()[:60]
        data["updated_at"] = now
        
        temp_path = path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
        
        return msg

    def _format_conversation_response(self, data: dict) -> dict:
        return {
            "conversation_id": data.get("conversation_id"),
            "project_id": data.get("project_id"),
            "title": data.get("title"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "message_count": len(data.get("messages", []))
        }

    def get_project_chat_history(self, project_id: str, date: str = None) -> list:
        conv_dir = self._get_project_conversations_dir(project_id)
        if not os.path.exists(conv_dir):
            return []
            
        history = []
        for file in os.listdir(conv_dir):
            if file.endswith(".json"):
                with open(os.path.join(conv_dir, file), "r") as f:
                    try:
                        data = json.load(f)
                        history.append(data)
                    except:
                        pass
        return history

class PostgresChatRepository(ChatRepository):
    def create_conversation(self, project_id: str, title: str = "New Conversation") -> dict:
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"
        db = SessionLocal()
        try:
            db_conv = Conversation(
                conversation_id=conversation_id,
                project_id=project_id,
                title=title,
                created_at=now,
                updated_at=now
            )
            db.add(db_conv)
            db.commit()
            return self._format_conversation_response(db_conv, 0)
        finally:
            db.close()

    def get_conversations(self, project_id: str) -> list:
        db = SessionLocal()
        try:
            convs = db.query(Conversation).filter(Conversation.project_id == project_id).all()
            res = []
            for c in convs:
                count = db.query(Message).filter(Message.conversation_id == c.conversation_id).count()
                res.append(self._format_conversation_response(c, count))
            return res
        finally:
            db.close()

    def get_conversation_response(self, project_id: str, conversation_id: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            c = db.query(Conversation).filter(Conversation.conversation_id == conversation_id, Conversation.project_id == project_id).first()
            if not c: return None
            count = db.query(Message).filter(Message.conversation_id == c.conversation_id).count()
            return self._format_conversation_response(c, count)
        finally:
            db.close()
            
    def delete_conversation(self, project_id: str, conversation_id: str) -> bool:
        db = SessionLocal()
        try:
            c = db.query(Conversation).filter(Conversation.conversation_id == conversation_id, Conversation.project_id == project_id).first()
            if not c: return False
            db.delete(c)
            db.commit()
            return True
        finally:
            db.close()

    def update_task_message(self, project_id: str, conversation_id: str, task_id: str, status: str) -> None:
        db = SessionLocal()
        try:
            msg = db.query(Message).filter(Message.task_id == task_id, Message.conversation_id == conversation_id).first()
            if msg:
                msg.status = status
                db.commit()
        finally:
            db.close()

    def add_message(self, project_id: str, conversation_id: str, role: str, content: str, 
                    execution_mode: str = None, task_id: str = None, status: str = None,
                    routing: dict = None, error: dict = None) -> dict:
        now = datetime.utcnow().isoformat() + "Z"
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        db = SessionLocal()
        try:
            c = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
            if not c: return None
            
            db_msg = Message(
                message_id=msg_id,
                conversation_id=conversation_id,
                project_id=project_id,
                role=role,
                content=content,
                execution_mode=execution_mode,
                task_id=task_id,
                status=status,
                routing=routing,
                error=error,
                created_at=now
            )
            db.add(db_msg)
            
            if role == "user" and c.title in (None, "", DEFAULT_TITLE):
                c.title = content.strip()[:60]
            c.updated_at = now
            
            db.commit()
            db.refresh(db_msg)
            
            return {
                "message_id": db_msg.message_id,
                "conversation_id": db_msg.conversation_id,
                "project_id": db_msg.project_id,
                "role": db_msg.role,
                "content": db_msg.content,
                "execution_mode": db_msg.execution_mode,
                "task_id": db_msg.task_id,
                "status": db_msg.status,
                "routing": db_msg.routing,
                "error": db_msg.error,
                "created_at": db_msg.created_at
            }
        finally:
            db.close()

    def get_project_chat_history(self, project_id: str, date: str = None) -> list:
        db = SessionLocal()
        try:
            convs = db.query(Conversation).filter(Conversation.project_id == project_id).all()
            history = []
            for c in convs:
                msgs = db.query(Message).filter(Message.conversation_id == c.conversation_id).all()
                msg_list = [{
                    "message_id": m.message_id,
                    "role": m.role,
                    "content": m.content,
                    "execution_mode": m.execution_mode,
                    "task_id": m.task_id,
                    "status": m.status,
                    "routing": m.routing,
                    "error": m.error,
                    "created_at": m.created_at
                } for m in msgs]
                history.append({
                    "conversation_id": c.conversation_id,
                    "project_id": c.project_id,
                    "title": c.title,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                    "messages": msg_list
                })
            return history
        finally:
            db.close()

    def _format_conversation_response(self, model: Conversation, message_count: int) -> dict:
        return {
            "conversation_id": model.conversation_id,
            "project_id": model.project_id,
            "title": model.title,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "message_count": message_count
        }

def get_chat_repository() -> ChatRepository:
    if settings.persistence_backend == "postgres":
        return PostgresChatRepository()
    return JsonChatRepository()
