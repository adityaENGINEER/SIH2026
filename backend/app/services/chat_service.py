import os
import re
import json
import uuid
from datetime import datetime
from app.core.config import settings

SAFE_ID = re.compile(r"^[A-Za-z0-9_\-]+$")
DEFAULT_TITLE = "New Conversation"

class ChatService:
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
        """Mirrors a finished agent run's terminal status onto its chat message."""
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
                        # Optional: filter by date if requested
                        history.append(data)
                    except:
                        pass
        return history

chat_service = ChatService()
