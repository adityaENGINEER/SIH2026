"""
Deliverable API routes — project-scoped.
All deliverables stored under D:\\SovereignAI\\storage\\outputs\\{project_id}\\
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List

from app.schemas.deliverables import DeliverableCreate, DeliverableResponse
from app.services.deliverable_service import deliverable_service

router = APIRouter()


def _err(data: dict):
    err = data.get("error", {})
    code = err.get("code", "UNKNOWN_ERROR")
    msg = err.get("message", "An error occurred.")
    status = 404 if "NOT_FOUND" in code or "MISSING" in code else 400
    raise HTTPException(status_code=status, detail={"code": code, "message": msg})


@router.post("/{project_id}/deliverables", response_model=DeliverableResponse)
def create_deliverable(project_id: str, req: DeliverableCreate):
    # project_id in path takes precedence (prevents cross-project writes)
    result = deliverable_service.create_deliverable(
        project_id=project_id,
        title=req.title,
        fmt=req.format,
        content=req.content or "",
        task_id=req.task_id,
        approval_id=req.approval_id,
    )
    if "error" in result:
        _err(result)
    return result


@router.get("/{project_id}/deliverables", response_model=List[DeliverableResponse])
def list_deliverables(project_id: str):
    return deliverable_service.list_deliverables(project_id)


@router.get("/{project_id}/deliverables/{deliverable_id}", response_model=DeliverableResponse)
def get_deliverable(project_id: str, deliverable_id: str):
    result = deliverable_service.get_deliverable(project_id, deliverable_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DELIVERABLE_NOT_FOUND", "message": "Deliverable not found."},
        )
    return result


@router.get("/{project_id}/deliverables/{deliverable_id}/download")
def download_deliverable(project_id: str, deliverable_id: str):
    result = deliverable_service.get_file_path(project_id, deliverable_id)
    if "error" in result:
        _err(result)
    return FileResponse(
        path=result["file_path"],
        filename=result["filename"],
        media_type="application/octet-stream",
    )
