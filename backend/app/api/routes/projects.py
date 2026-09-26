import os
from fastapi import APIRouter, HTTPException
from typing import List
from app.core.config import settings
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import project_service

router = APIRouter()

@router.post("", response_model=ProjectResponse)
def create_project(req: ProjectCreate):
    res = project_service.create_project(
        name=req.name,
        description=req.description,
        project_type=req.project_type
    )
    return res

@router.get("", response_model=List[ProjectResponse])
def get_projects():
    return project_service.get_projects()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    p = project_service.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail={"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found"}})
    return p

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, req: ProjectUpdate):
    updates = req.dict(exclude_unset=True)
    p = project_service.update_project(project_id, updates)
    if not p:
        raise HTTPException(status_code=404, detail={"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found"}})
    return p

@router.delete("/{project_id}")
def delete_project(project_id: str):
    success = project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail={"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found"}})
    return {"status": "ok"}

# --- Conversations & Chat ---

from app.schemas.chat import ConversationCreate, ConversationResponse, MessageRequest, MessageResponse
from app.services.chat_service import chat_service
from app.services.ollama_service import ollama_service
from app.agents.tuffy.agent import agent
from app.services.document_service import document_service
from app.services.model_router import model_router
from app.services.security_service import security_service
from app.services.vector_store import vector_store
from app.core.request_context import set_context
from fastapi.responses import FileResponse


def _require_project_document(project_id: str, document_id: str) -> dict:
    """404 unless the document exists AND belongs to project_id (no cross-project metadata leak)."""
    meta = document_service.get_metadata(document_id)
    if "error" in meta or meta.get("project_id") != project_id:
        raise HTTPException(status_code=404, detail={"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Document not found in this project."}})
    return meta

@router.post("/{project_id}/conversations", response_model=ConversationResponse)
def create_conversation(project_id: str, req: ConversationCreate):
    return chat_service.create_conversation(project_id, req.title)

@router.get("/{project_id}/conversations", response_model=List[ConversationResponse])
def get_conversations(project_id: str):
    return chat_service.get_conversations(project_id)

@router.get("/{project_id}/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(project_id: str, conversation_id: str):
    c = chat_service.get_conversation_response(project_id, conversation_id)
    if not c:
        raise HTTPException(status_code=404, detail={"error": {"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}})
    return c

@router.delete("/{project_id}/conversations/{conversation_id}")
def delete_conversation(project_id: str, conversation_id: str):
    success = chat_service.delete_conversation(project_id, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail={"error": {"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}})
    return {"status": "ok"}

@router.get("/{project_id}/chat/history")
def get_chat_history(project_id: str, date: str = None):
    return chat_service.get_project_chat_history(project_id, date)

from fastapi import BackgroundTasks

@router.post("/{project_id}/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(project_id: str, conversation_id: str, req: MessageRequest, background_tasks: BackgroundTasks):
    c = chat_service.get_conversation(project_id, conversation_id)
    if not c:
        raise HTTPException(status_code=404, detail={"error": {"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found"}})
        
    for doc_id in req.document_ids or []:
        _require_project_document(project_id, doc_id)
    # Only a single explicitly targeted document narrows retrieval; otherwise RAG is scoped by project_id.
    doc_id = req.document_ids[0] if len(req.document_ids or []) == 1 else None
    doc_meta = document_service.get_metadata(doc_id) if doc_id else None

    chat_service.add_message(project_id, conversation_id, "user", req.message)

    set_context(project_id=project_id)
    routing = model_router.route(req.message, doc_meta, await ollama_service.list_models())

    mode = req.mode
    if mode == "auto":
        mode = "agent"
    if routing["purpose"] == "vision":
        mode = "agent"

    if mode == "chat":
        res = await ollama_service.generate(model=routing["model"], prompt=req.message)
        if "error" in res:
            return chat_service.add_message(
                project_id=project_id, conversation_id=conversation_id, role="assistant",
                content=f"Model inference failed: {res['error'].get('message')}",
                execution_mode="chat", status="failed", routing=routing, error=res["error"],
            )
        return chat_service.add_message(
            project_id=project_id, conversation_id=conversation_id, role="assistant",
            content=res.get("response", "").strip(), execution_mode="chat", status="completed", routing=routing,
        )

    task_id = agent.create_task(
        user_request=req.message,
        document_id=doc_id,
        project_id=project_id,
        conversation_id=conversation_id,
        routing=routing,
    )
    background_tasks.add_task(agent.run_task, task_id)
    return chat_service.add_message(
        project_id=project_id, conversation_id=conversation_id, role="assistant",
        content="Task initiated.", execution_mode="agent", task_id=task_id, status="running", routing=routing,
    )

# --- Documents ---

@router.get("/{project_id}/documents")
def get_project_documents(project_id: str):
    # Iterate all documents and return those that match project_id
    # (Since there's no DB, we have to scan the upload directory)
    docs = []
    if os.path.exists(settings.upload_dir):
        for d in os.listdir(settings.upload_dir):
            meta = document_service.get_metadata(d)
            if "error" not in meta and meta.get("project_id") == project_id:
                docs.append(meta)
    return docs

@router.get("/{project_id}/documents/{document_id}")
def get_project_document(project_id: str, document_id: str):
    return _require_project_document(project_id, document_id)

@router.get("/{project_id}/documents/{document_id}/download")
def download_project_document(project_id: str, document_id: str):
    _require_project_document(project_id, document_id)
    result = document_service.get_file_path(document_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return FileResponse(path=result["file_path"], filename=result["original_filename"])

@router.get("/{project_id}/documents/{document_id}/sources")
def get_project_document_sources(project_id: str, document_id: str):
    _require_project_document(project_id, document_id)
    sources = [
        {"document_id": m.get("document_id"), "chunk_id": m.get("chunk_id"), "text": m.get("text"), "source": m.get("source")}
        for m in vector_store.metadata if m.get("document_id") == document_id
    ]
    return {"document_id": document_id, "sources": sources}

@router.delete("/{project_id}/documents/{document_id}")
def delete_project_document(project_id: str, document_id: str):
    _require_project_document(project_id, document_id)
    result = document_service.delete_document(document_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# --- Agent Runs ---

def _require_project_run(project_id: str, run_id: str):
    state = agent.get_state(run_id)
    if not state or state.project_id != project_id:
        raise HTTPException(status_code=404, detail={"error": {"code": "AGENT_RUN_NOT_FOUND", "message": "Agent run not found."}})
    return agent.recover_if_orphaned(state)

@router.get("/{project_id}/agent-runs")
def get_project_agent_runs(project_id: str):
    tasks = agent.get_tasks_for_project(project_id)
    return [agent.recover_if_orphaned(t).model_dump() for t in tasks]

@router.get("/{project_id}/agent-runs/{run_id}")
def get_project_agent_run(project_id: str, run_id: str):
    return _require_project_run(project_id, run_id).model_dump()

@router.post("/{project_id}/agent-runs/{run_id}/cancel")
def cancel_project_agent_run(project_id: str, run_id: str):
    _require_project_run(project_id, run_id)
    return agent.request_cancel(run_id).model_dump()

# --- Security ---

@router.get("/{project_id}/security/events")
def get_project_security_events(project_id: str):
    return security_service.get_events(project_id)

@router.get("/{project_id}/security/summary")
def get_project_security_summary(project_id: str):
    return security_service.get_summary(project_id)

