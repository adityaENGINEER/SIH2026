from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Project(Base):
    __tablename__ = "projects"
    project_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    project_type = Column(String, default="general")
    status = Column(String, default="active")
    created_at = Column(String)
    updated_at = Column(String)

class Conversation(Base):
    __tablename__ = "conversations"
    conversation_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    title = Column(String)
    created_at = Column(String)
    updated_at = Column(String)

class Message(Base):
    __tablename__ = "messages"
    message_id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id", ondelete="CASCADE"), index=True)
    project_id = Column(String, index=True)
    role = Column(String)
    content = Column(String)
    execution_mode = Column(String, nullable=True)
    task_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True)
    routing = Column(JSON, nullable=True)
    error = Column(JSON, nullable=True)
    created_at = Column(String)

class Document(Base):
    __tablename__ = "documents"
    document_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    original_filename = Column(String)
    status = Column(String)
    extracted_text = Column(String, nullable=True)
    pages = Column(JSON, nullable=True)
    created_at = Column(String)

class Approval(Base):
    __tablename__ = "approvals"
    approval_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    conversation_id = Column(String, nullable=True, index=True)
    task_id = Column(String, nullable=True, index=True)
    agent_run_id = Column(String, nullable=True, index=True)
    deliverable_id = Column(String, nullable=True, index=True)
    title = Column(String)
    status = Column(String, default="DRAFT")
    created_at = Column(String)
    updated_at = Column(String)
    submitted_at = Column(String, nullable=True)
    reviewed_at = Column(String, nullable=True)
    approver_name = Column(String, nullable=True)
    employee_id = Column(String, nullable=True)
    review_comment = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    approval_reason = Column(String, nullable=True)
    signature_status = Column(String, default="unsigned")
    source_document_ids = Column(JSON, default=[])
    output_document_ids = Column(JSON, default=[])

class Deliverable(Base):
    __tablename__ = "deliverables"
    deliverable_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), index=True)
    title = Column(String)
    type = Column(String)
    status = Column(String)
    file_path = Column(String)
    created_at = Column(String)

class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    timestamp = Column(String, index=True)
    details = Column(JSON)
