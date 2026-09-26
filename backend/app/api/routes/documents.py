from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.services.document_service import document_service
from app.services.document_extractor import document_extractor
from app.schemas.documents import DocumentUploadResponse

router = APIRouter()

from app.services.indexing_service import indexing_service
import asyncio

from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), project_id: Optional[str] = Form(None)):
    from app.services.project_service import project_service
    if project_id and not project_service.get_project(project_id):
        raise HTTPException(status_code=404, detail={"code": "PROJECT_NOT_FOUND", "message": "Project not found."})
    result = document_service.save_upload(file, project_id)
    if "error" in result:
        return result
        
    doc_id = result["document_id"]
    
    # Extract immediately
    extract_result = document_extractor.extract(doc_id)
    
    # Try indexing if extraction had content
    # If requires OCR, it will be skipped by indexing_service and marked
    await indexing_service.index_document(doc_id)
    
    # Re-fetch metadata for the final status
    final_meta = document_service.get_metadata(doc_id)
    
    return {
        "document_id": final_meta.get("document_id"),
        "filename": final_meta.get("original_filename"),
        "content_type": final_meta.get("content_type"),
        "size_bytes": final_meta.get("size_bytes"),
        "status": final_meta.get("status"),
        "storage_status": "stored",
        "content_status": final_meta.get("content_status", "pending"),
        "index_status": final_meta.get("index_status", "not_indexed")
    }

def _require_unscoped(document_id: str):
    """Project-owned documents are only reachable via /api/projects/{project_id}/documents/..."""
    meta = document_service.get_metadata(document_id)
    if "error" not in meta and meta.get("project_id"):
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."})
    return meta

@router.get("/documents/{document_id}")
async def get_document_metadata(document_id: str):
    return _require_unscoped(document_id)

@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    _require_unscoped(document_id)
    result = document_service.get_file_path(document_id)
    if "error" in result:
        return result
        
    file_path = result["file_path"]
    filename = result["original_filename"]
    
    return FileResponse(path=file_path, filename=filename)

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    _require_unscoped(document_id)
    return document_service.delete_document(document_id)

@router.get("/documents/{document_id}/content")
async def get_document_content(document_id: str):
    _require_unscoped(document_id)
    result = document_extractor.extract(document_id)
    if "error" in result:
        return result
        
    return {
        "document_id": result.get("document_id"),
        "document_type": result.get("document_type"),
        "content_status": result.get("content_status"),
        "requires_ocr": result.get("requires_ocr"),
        "content": result
    }

from app.services.vector_store import vector_store

@router.get("/documents/{document_id}/sources")
async def get_document_sources(document_id: str):
    _require_unscoped(document_id)
    sources = []
    for meta in vector_store.metadata:
        if meta.get("document_id") == document_id:
            sources.append({
                "document_id": meta.get("document_id"),
                "chunk_id": meta.get("chunk_id"),
                "text": meta.get("text"),
                "source": meta.get("source")
            })
    return {"document_id": document_id, "sources": sources}
