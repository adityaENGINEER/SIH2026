from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ocr_service import ocr_service

router = APIRouter()

class OCRProcessRequest(BaseModel):
    document_id: str

@router.post("/ocr/process")
async def process_ocr(request: OCRProcessRequest):
    return ocr_service.process(request.document_id)

@router.get("/ocr/{ocr_id}")
async def get_ocr_result(document_id: str, ocr_id: str):
    return ocr_service.get_result(document_id, ocr_id)
