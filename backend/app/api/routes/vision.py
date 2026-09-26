from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.vision_service import vision_service

router = APIRouter()

class VisionAnalyzeRequest(BaseModel):
    file_path: str
    prompt: Optional[str] = None

@router.post("/analyze")
async def analyze_image(request: VisionAnalyzeRequest):
    res = await vision_service.analyze(request.file_path, request.prompt)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/{vision_id}")
async def get_vision_result(vision_id: str):
    res = vision_service.get_result(vision_id)
    if not res:
        raise HTTPException(status_code=404, detail="Vision result not found")
    return res
