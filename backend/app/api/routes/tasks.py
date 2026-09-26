from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.agents.tuffy.agent import agent

router = APIRouter()

from typing import Dict, Any, Optional


def _unscoped_state(task_id: str):
    """Project-owned runs are only served under /api/projects/{project_id}/agent-runs."""
    state = agent.get_state(task_id)
    if state and state.project_id:
        return None
    return state

class TaskCreateRequest(BaseModel):
    user_request: str
    document_id: Optional[str] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None

@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    if not request.user_request.strip():
        raise HTTPException(status_code=400, detail="User request cannot be empty")
        
    task_id = agent.create_task(
        request.user_request, 
        request.document_id,
        request.project_id,
        request.conversation_id
    )
    state = _unscoped_state(task_id)
    
    return {
        "task_id": task_id,
        "status": state.status,
        "created_at": state.created_at
    }

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    state = _unscoped_state(task_id)
    if not state:
        return {"error": {"code": "TASK_NOT_FOUND", "message": "Task not found."}}
        
    return state.model_dump()

@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str):
    if not _unscoped_state(task_id):
        return {"error": {"code": "TASK_NOT_FOUND", "message": "Task not found."}}
    return await agent.run_task(task_id)

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    state = _unscoped_state(task_id)
    if not state:
        return {"error": {"code": "TASK_NOT_FOUND", "message": "Task not found."}}
        
    return {
        "task_id": state.task_id,
        "status": state.status,
        "current_step": state.current_step,
        "step_count": state.step_count
    }

@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    state = _unscoped_state(task_id)
    if not state:
        return {"error": {"code": "TASK_NOT_FOUND", "message": "Task not found."}}
        
    if state.status == "completed":
        return {"result": state.final_result}
    elif state.status == "failed":
        return {"error": state.error}
    else:
        return {"error": {"code": "TASK_INCOMPLETE", "message": f"Task is currently in status: {state.status}"}}

@router.get("/tasks/{task_id}/agent-log")
async def get_task_log(task_id: str):
    state = _unscoped_state(task_id)
    if not state:
        return {"error": {"code": "TASK_NOT_FOUND", "message": "Task not found."}}
        
    logs = [obs.model_dump() for obs in state.observations]
    return {"task_id": task_id, "logs": logs}

from fastapi.responses import FileResponse
import os
from app.core.config import settings

@router.get("/tasks/{task_id}/download")
async def download_task_output(task_id: str):
    outputs_dir = os.path.join(settings.storage_root, "outputs", task_id)
    file_path = os.path.join(outputs_dir, "Industrial_Authorization.docx")
    
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.storage_root)):
        return {"error": {"code": "OUTPUT_INVALID", "message": "Invalid file path."}}

    if not os.path.exists(file_path):
        return {"error": {"code": "OUTPUT_NOT_FOUND", "message": "Output document not found for this task."}}

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="Industrial_Authorization.docx"
    )
