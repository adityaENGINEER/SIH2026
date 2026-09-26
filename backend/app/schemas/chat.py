from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    conversation_id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

class MessageRequest(BaseModel):
    message: str
    document_ids: Optional[List[str]] = Field(default_factory=list)
    mode: Optional[str] = "auto" # auto, chat, agent

class MessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    project_id: str
    role: str
    content: str
    execution_mode: Optional[str] = None
    task_id: Optional[str] = None
    status: Optional[str] = None
    routing: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    created_at: str
