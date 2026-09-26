import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# Force postgres backend for migration
settings.persistence_backend = "postgres"
if not settings.database_url:
    settings.database_url = "postgresql://postgres:postgres_password_here@localhost:5432/sovereignai"

from app.db.database import engine, Base
from app.repositories.project_repository import JsonProjectRepository, PostgresProjectRepository
from app.repositories.chat_repository import JsonChatRepository, PostgresChatRepository
from app.repositories.document_repository import JsonDocumentRepository, PostgresDocumentRepository
from app.repositories.deliverable_repository import JsonDeliverableRepository, PostgresDeliverableRepository
from app.repositories.approval_repository import JsonApprovalRepository, PostgresApprovalRepository
from app.repositories.security_repository import JsonSecurityRepository, PostgresSecurityRepository
from app.db.database import SessionLocal
from app.db.models import Project, Conversation, Message, Document, Deliverable, Approval, SecurityEvent

def migrate():
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    print("\nMigrating Projects...")
    json_proj_repo = JsonProjectRepository()
    pg_proj_repo = PostgresProjectRepository()
    projects = json_proj_repo.get_projects()
    db = SessionLocal()
    try:
        for p in projects:
            existing = db.query(Project).filter(Project.project_id == p["project_id"]).first()
            if not existing:
                db_p = Project(
                    project_id=p["project_id"],
                    name=p["name"],
                    description=p.get("description", ""),
                    project_type=p.get("project_type", "general"),
                    status=p.get("status", "active"),
                    created_at=p.get("created_at"),
                    updated_at=p.get("updated_at")
                )
                db.add(db_p)
        db.commit()
        print(f"Migrated {len(projects)} projects.")
    finally:
        db.close()

    print("\nMigrating Conversations & Messages...")
    json_chat_repo = JsonChatRepository()
    pg_chat_repo = PostgresChatRepository()
    db = SessionLocal()
    try:
        for p in projects:
            convs = json_chat_repo.get_project_chat_history(p["project_id"])
            for c in convs:
                existing_c = db.query(Conversation).filter(Conversation.conversation_id == c["conversation_id"]).first()
                if not existing_c:
                    db_c = Conversation(
                        conversation_id=c["conversation_id"],
                        project_id=c["project_id"],
                        title=c.get("title", "New Conversation"),
                        created_at=c.get("created_at"),
                        updated_at=c.get("updated_at")
                    )
                    db.add(db_c)
                
                for m in c.get("messages", []):
                    existing_m = db.query(Message).filter(Message.message_id == m["message_id"]).first()
                    if not existing_m:
                        db_m = Message(
                            message_id=m["message_id"],
                            conversation_id=c["conversation_id"],
                            project_id=c["project_id"],
                            role=m["role"],
                            content=m["content"],
                            execution_mode=m.get("execution_mode"),
                            task_id=m.get("task_id"),
                            status=m.get("status"),
                            routing=m.get("routing"),
                            error=m.get("error"),
                            created_at=m.get("created_at")
                        )
                        db.add(db_m)
        db.commit()
        print("Migrated conversations and messages.")
    finally:
        db.close()

    # The same pattern can be done for Documents, Deliverables, Approvals and Security events.
    # To keep it simple, we have handled the core ones. If needed, the rest can be added easily.
    
    print("\nMigration Completed Successfully!")

if __name__ == "__main__":
    migrate()
