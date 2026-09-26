import os
import json
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Document

class DocumentRepository(ABC):
    @abstractmethod
    def create_document_metadata(self, document_id: str, project_id: str, original_filename: str) -> dict:
        pass

    @abstractmethod
    def update_document_metadata(self, document_id: str, project_id: str, updates: dict) -> Optional[dict]:
        pass

    @abstractmethod
    def get_document_metadata(self, document_id: str, project_id: str) -> Optional[dict]:
        pass
        
    @abstractmethod
    def delete_document_metadata(self, document_id: str, project_id: str) -> bool:
        pass


class JsonDocumentRepository(DocumentRepository):
    def _get_doc_dir(self, document_id: str) -> str:
        return os.path.join(settings.upload_dir, document_id)

    def _get_meta_path(self, document_id: str) -> str:
        return os.path.join(self._get_doc_dir(document_id), "metadata.json")

    def create_document_metadata(self, document_id: str, project_id: str, original_filename: str) -> dict:
        doc_dir = self._get_doc_dir(document_id)
        os.makedirs(doc_dir, exist_ok=True)
        now = datetime.utcnow().isoformat() + "Z"
        
        meta = {
            "document_id": document_id,
            "project_id": project_id,
            "original_filename": original_filename,
            "status": "uploading",
            "extracted_text": None,
            "pages": [],
            "created_at": now
        }
        with open(self._get_meta_path(document_id), "w") as f:
            json.dump(meta, f, indent=2)
            
        return meta

    def update_document_metadata(self, document_id: str, project_id: str, updates: dict) -> Optional[dict]:
        meta_path = self._get_meta_path(document_id)
        if not os.path.exists(meta_path):
            return None
            
        with open(meta_path, "r") as f:
            data = json.load(f)
            
        if data.get("project_id") != project_id:
            return None
            
        for k, v in updates.items():
            data[k] = v
            
        temp_path = meta_path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, meta_path)
        
        return data

    def get_document_metadata(self, document_id: str, project_id: str) -> Optional[dict]:
        meta_path = self._get_meta_path(document_id)
        if not os.path.exists(meta_path):
            return None
            
        with open(meta_path, "r") as f:
            data = json.load(f)
            
        if data.get("project_id") != project_id:
            return None
        return data

    def delete_document_metadata(self, document_id: str, project_id: str) -> bool:
        meta_path = self._get_meta_path(document_id)
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                data = json.load(f)
            if data.get("project_id") == project_id:
                os.remove(meta_path)
                return True
        return False


class PostgresDocumentRepository(DocumentRepository):
    # Important: In Postgres mode, we STILL use the filesystem for the actual file
    # We only store the *metadata* in PostgreSQL.
    
    def create_document_metadata(self, document_id: str, project_id: str, original_filename: str) -> dict:
        now = datetime.utcnow().isoformat() + "Z"
        db = SessionLocal()
        try:
            db_doc = Document(
                document_id=document_id,
                project_id=project_id,
                original_filename=original_filename,
                status="uploading",
                extracted_text=None,
                pages=[],
                created_at=now
            )
            db.add(db_doc)
            db.commit()
            db.refresh(db_doc)
            return self._to_dict(db_doc)
        finally:
            db.close()

    def update_document_metadata(self, document_id: str, project_id: str, updates: dict) -> Optional[dict]:
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.document_id == document_id, Document.project_id == project_id).first()
            if not doc: return None
            
            for k, v in updates.items():
                if hasattr(doc, k):
                    setattr(doc, k, v)
                    
            db.commit()
            db.refresh(doc)
            return self._to_dict(doc)
        finally:
            db.close()

    def get_document_metadata(self, document_id: str, project_id: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.document_id == document_id, Document.project_id == project_id).first()
            return self._to_dict(doc) if doc else None
        finally:
            db.close()

    def delete_document_metadata(self, document_id: str, project_id: str) -> bool:
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.document_id == document_id, Document.project_id == project_id).first()
            if not doc: return False
            db.delete(doc)
            db.commit()
            return True
        finally:
            db.close()

    def _to_dict(self, model: Document) -> dict:
        return {
            "document_id": model.document_id,
            "project_id": model.project_id,
            "original_filename": model.original_filename,
            "status": model.status,
            "extracted_text": model.extracted_text,
            "pages": model.pages,
            "created_at": model.created_at
        }

def get_document_repository() -> DocumentRepository:
    if settings.persistence_backend == "postgres":
        return PostgresDocumentRepository()
    return JsonDocumentRepository()
