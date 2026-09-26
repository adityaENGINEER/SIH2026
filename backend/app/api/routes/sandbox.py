from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.sandbox import sandbox_service

router = APIRouter()

class SandboxExecuteRequest(BaseModel):
    code: str

@router.post("/execute")
async def execute_code(request: SandboxExecuteRequest):
    try:
        res = sandbox_service.execute(request.code)
        return {
            "execution_id": res.execution_id,
            "status": res.status,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "exit_code": res.exit_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    res = sandbox_service.get_execution(execution_id)
    if not res:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "execution_id": res.execution_id,
        "status": res.status,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "exit_code": res.exit_code
    }
