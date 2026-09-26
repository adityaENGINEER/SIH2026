import os
import uuid
import json
import shutil
from datetime import datetime
from fastapi import UploadFile
import logging

from app.core.config import settings
from app.schemas.documents import DocumentMetadata
from app.repositories.document_repository import get_document_repository

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".txt",
    ".xlsx", ".csv",
    ".png", ".jpg", ".jpeg"
}

class DocumentService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        self.max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        self.repo = get_document_repository()

    def _is_safe_filename(self, filename: str) -> bool:
        if not filename:
            return False
        if ".." in filename or "/" in filename or "\\" in filename:
            return False
        return True

    def _get_extension(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        return ext.lower()

    def _is_allowed_extension(self, ext: str) -> bool:
        return ext in ALLOWED_EXTENSIONS

    def save_upload(self, file: UploadFile, project_id: str = None) -> dict:
        logger.info("Document upload started")
        
        original_filename = file.filename or "unknown"
        if not self._is_safe_filename(original_filename):
            logger.error("Upload failed: unsafe filename")
            return {"error": {"code": "INVALID_FILE_TYPE", "message": "Invalid or unsafe filename."}}

        ext = self._get_extension(original_filename)
        if not self._is_allowed_extension(ext):
            logger.error(f"Upload failed: unsupported file type {ext}")
            return {"error": {"code": "INVALID_FILE_TYPE", "message": f"Unsupported file type: {ext}"}}

        doc_id = f"doc_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        doc_dir = os.path.join(self.upload_dir, doc_id)
        
        if not os.path.abspath(doc_dir).startswith(os.path.abspath(self.upload_dir)):
            return {"error": {"code": "UPLOAD_FAILED", "message": "Invalid storage path generated."}}
            
        os.makedirs(doc_dir, exist_ok=True)
        
        stored_filename = f"{doc_id}{ext}"
        file_path = os.path.join(doc_dir, stored_filename)
        
        try:
            size_bytes = 0
            with open(file_path, "wb") as buffer:
                while chunk := file.file.read(8192):
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        buffer.close()
                        shutil.rmtree(doc_dir)
                        return {"error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds the {settings.max_upload_size_mb} MB limit."}}
                    buffer.write(chunk)
            
            # Use repository to save metadata
            self.repo.create_document_metadata(doc_id, project_id, original_filename)
            
            updates = {
                "stored_filename": stored_filename,
                "content_type": file.content_type or "application/octet-stream",
                "extension": ext,
                "size_bytes": size_bytes,
                "storage_path": file_path,
                "status": "uploaded"
            }
            meta_result = self.repo.update_document_metadata(doc_id, project_id, updates)
            
            if not meta_result:
                raise Exception("Failed to update metadata via repository")
                
            logger.info(f"Document uploaded. ID: {doc_id}, Type: {ext}, Size: {size_bytes}")
            
            # For backward compatibility return same shape as before
            return DocumentMetadata(**meta_result).model_dump()
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            if os.path.exists(doc_dir):
                shutil.rmtree(doc_dir)
            return {"error": {"code": "UPLOAD_FAILED", "message": "An error occurred while saving the file."}}

    def get_metadata(self, document_id: str, project_id: str) -> dict:
        meta = self.repo.get_document_metadata(document_id, project_id)
        if not meta:
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Document metadata not found."}}
        return meta

    def update_metadata(self, document_id: str, project_id: str, updates: dict) -> dict:
        meta = self.repo.update_document_metadata(document_id, project_id, updates)
        if not meta:
            return {"error": {"code": "UPDATE_FAILED", "message": "Failed to update metadata."}}
        return meta

    def get_file_path(self, document_id: str, project_id: str) -> dict:
        meta_result = self.get_metadata(document_id, project_id)
        if "error" in meta_result:
            return meta_result
            
        storage_path = meta_result.get("storage_path")
        if not storage_path or not os.path.exists(storage_path):
            return {"error": {"code": "FILE_NOT_FOUND", "message": "Physical file not found on disk."}}
            
        if not os.path.abspath(storage_path).startswith(os.path.abspath(self.upload_dir)):
            return {"error": {"code": "FILE_NOT_FOUND", "message": "Physical file not found on disk."}}
            
        return {"file_path": storage_path, "original_filename": meta_result.get("original_filename")}

    def delete_document(self, document_id: str, project_id: str) -> dict:
        doc_dir = os.path.join(self.upload_dir, document_id)
        
        # Remove from vector store
        from app.services.vector_store import vector_store
        try:
            vector_store.remove_document(document_id)
        except Exception as ve:
            logger.warning(f"Could not remove document {document_id} from vector store: {ve}")

        # Delete from repository
        self.repo.delete_document_metadata(document_id, project_id)

        # Delete physical files
        if os.path.exists(doc_dir) and os.path.abspath(doc_dir).startswith(os.path.abspath(self.upload_dir)):
            shutil.rmtree(doc_dir, ignore_errors=True)
            
        logger.info(f"Document deleted: {document_id}")
        return {"status": "success", "message": f"Document {document_id} deleted."}

document_service = DocumentService()
