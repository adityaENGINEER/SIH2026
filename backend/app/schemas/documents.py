from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentMetadata(BaseModel):
    document_id: str
    project_id: Optional[str] = None
    original_filename: str
    stored_filename: str
    content_type: str
    extension: str
    size_bytes: int
    created_at: str
    storage_path: str
    status: str
    content_status: str = "pending"
    index_status: str = "not_indexed"
    requires_ocr: bool = False

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    storage_status: str = "stored"
    content_status: str = "pending"
    index_status: str = "not_indexed"
