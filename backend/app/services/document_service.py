import os
import uuid
import json
import shutil
from datetime import datetime
from fastapi import UploadFile
import logging

from app.core.config import settings
from app.schemas.documents import DocumentMetadata

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
        
        # Validation: filename safety
        original_filename = file.filename or "unknown"
        if not self._is_safe_filename(original_filename):
            logger.error("Upload failed: unsafe filename")
            return {"error": {"code": "INVALID_FILE_TYPE", "message": "Invalid or unsafe filename."}}

        # Validation: extension
        ext = self._get_extension(original_filename)
        if not self._is_allowed_extension(ext):
            logger.error(f"Upload failed: unsupported file type {ext}")
            return {"error": {"code": "INVALID_FILE_TYPE", "message": f"Unsupported file type: {ext}"}}

        # Generate unique ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        doc_dir = os.path.join(self.upload_dir, doc_id)
        
        # Security: prevent path traversal during folder creation
        if not os.path.abspath(doc_dir).startswith(os.path.abspath(self.upload_dir)):
            return {"error": {"code": "UPLOAD_FAILED", "message": "Invalid storage path generated."}}
            
        os.makedirs(doc_dir, exist_ok=True)
        
        # Store file
        # We use the doc_id as the stored filename to guarantee no collisions
        stored_filename = f"{doc_id}{ext}"
        file_path = os.path.join(doc_dir, stored_filename)
        
        try:
            # Check size by reading chunks
            size_bytes = 0
            with open(file_path, "wb") as buffer:
                while chunk := file.file.read(8192):
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        buffer.close()
                        shutil.rmtree(doc_dir) # cleanup
                        return {"error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds the {settings.max_upload_size_mb} MB limit."}}
                    buffer.write(chunk)
            
            # Save metadata
            metadata = DocumentMetadata(
                document_id=doc_id,
                project_id=project_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                content_type=file.content_type or "application/octet-stream",
                extension=ext,
                size_bytes=size_bytes,
                created_at=datetime.utcnow().isoformat() + "Z",
                storage_path=file_path,
                status="uploaded"
            )
            
            meta_path = os.path.join(doc_dir, "metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(metadata.model_dump_json(indent=2))
                
            logger.info(f"Document uploaded. ID: {doc_id}, Type: {ext}, Size: {size_bytes}")
            
            return metadata.model_dump()
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            if os.path.exists(doc_dir):
                shutil.rmtree(doc_dir)
            return {"error": {"code": "UPLOAD_FAILED", "message": "An error occurred while saving the file."}}

    def get_metadata(self, document_id: str) -> dict:
        doc_dir = os.path.join(self.upload_dir, document_id)
        
        # Security check
        if not os.path.abspath(doc_dir).startswith(os.path.abspath(self.upload_dir)):
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."}}
            
        meta_path = os.path.join(doc_dir, "metadata.json")
        
        if not os.path.exists(meta_path):
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Document metadata not found."}}
            
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Failed to read document metadata."}}

    def update_metadata(self, document_id: str, updates: dict) -> dict:
        meta_result = self.get_metadata(document_id)
        if "error" in meta_result:
            return meta_result
            
        doc_dir = os.path.join(self.upload_dir, document_id)
        meta_path = os.path.join(doc_dir, "metadata.json")
        
        meta_result.update(updates)
        
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_result, f, indent=2)
            return meta_result
        except Exception as e:
            logger.error(f"Failed to update metadata for {document_id}: {e}")
            return {"error": {"code": "UPDATE_FAILED", "message": "Failed to update metadata."}}

    def get_file_path(self, document_id: str) -> dict:
        meta_result = self.get_metadata(document_id)
        if "error" in meta_result:
            return meta_result
            
        storage_path = meta_result.get("storage_path")
        if not storage_path or not os.path.exists(storage_path):
            return {"error": {"code": "FILE_NOT_FOUND", "message": "Physical file not found on disk."}}
            
        # Security check
        if not os.path.abspath(storage_path).startswith(os.path.abspath(self.upload_dir)):
            return {"error": {"code": "FILE_NOT_FOUND", "message": "Physical file not found on disk."}}
            
        return {"file_path": storage_path, "original_filename": meta_result.get("original_filename")}

    def delete_document(self, document_id: str) -> dict:
        doc_dir = os.path.join(self.upload_dir, document_id)
        
        # Security check
        if not os.path.abspath(doc_dir).startswith(os.path.abspath(self.upload_dir)):
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."}}
            
        if not os.path.exists(doc_dir):
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."}}
            
        try:
            # Remove from vector store
            from app.services.vector_store import vector_store
            try:
                vector_store.remove_document(document_id)
            except Exception as ve:
                logger.warning(f"Could not remove document {document_id} from vector store: {ve}")

            shutil.rmtree(doc_dir)
            logger.info(f"Document deleted: {document_id}")
            return {"status": "success", "message": f"Document {document_id} deleted."}
        except Exception as e:
            logger.error(f"Document delete failed: {str(e)}")
            return {"error": {"code": "DOCUMENT_DELETE_FAILED", "message": "Could not delete document files."}}

document_service = DocumentService()
