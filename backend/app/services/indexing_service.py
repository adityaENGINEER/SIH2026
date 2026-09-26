import os
import json
import logging
import numpy as np
from typing import Dict, Any

from app.services.document_service import document_service
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

class IndexingService:
    def __init__(self):
        # Initialize store
        try:
            vector_store.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")

    async def index_document(self, document_id: str) -> Dict[str, Any]:
        """
        Indexes a document by reading its content.json, chunking, embedding, and adding to FAISS.
        """
        meta_result = document_service.get_metadata(document_id)
        if "error" in meta_result:
            return meta_result

        doc_dir = os.path.dirname(meta_result["storage_path"])
        content_cache_path = os.path.join(doc_dir, "content.json")

        if not os.path.exists(content_cache_path):
            return {"error": {"code": "CONTENT_NOT_FOUND", "message": "Content not extracted yet. Call /content first."}}

        try:
            with open(content_cache_path, "r", encoding="utf-8") as f:
                content_cache = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read content for {document_id}: {e}")
            return {"error": {"code": "READ_ERROR", "message": "Could not read content cache."}}

        status = content_cache.get("content_status", "")
        if status in ["empty", "no_extractable_text"] and not content_cache.get("ocr_used"):
            document_service.update_metadata(document_id, {"index_status": "requires_ocr"})
            return {"error": {"code": "NO_INDEXABLE_CONTENT", "message": "Document has no usable text."}}

        text = content_cache.get("text", "")
        if not text.strip():
            return {"error": {"code": "EMPTY_DOCUMENT", "message": "Document is empty."}}

        # Duplicate check (skip if already in manifest/metadata)
        # Note: MVP skipping
        if any(m.get("document_id") == document_id for m in vector_store.metadata):
            logger.info(f"Document {document_id} already indexed, skipping.")
            return {
                "document_id": document_id,
                "status": "already_indexed"
            }

        # Update status to indexing
        document_service.update_metadata(document_id, {"index_status": "indexing"})
        
        # 1. Chunking
        chunks = chunking_service.chunk_document(content_cache)
        if not chunks:
            document_service.update_metadata(document_id, {"index_status": "failed"})
            return {"error": {"code": "NO_INDEXABLE_CONTENT", "message": "No chunks generated."}}

        # 2. Embedding
        texts_to_embed = [c["text"] for c in chunks]
        
        is_available = await embedding_service.verify_availability()
        if not is_available:
            document_service.update_metadata(document_id, {"index_status": "failed"})
            return {"error": {"code": "EMBEDDING_MODEL_UNAVAILABLE", "message": "Embedding model not found in Ollama."}}

        embeddings = await embedding_service.embed_texts(texts_to_embed)
        
        valid_vectors = []
        valid_metadata = []
        
        for chunk, emb in zip(chunks, embeddings):
            if emb and len(emb) > 0:
                valid_vectors.append(emb)
                valid_metadata.append(chunk)

        if not valid_vectors:
            document_service.update_metadata(document_id, {"index_status": "failed"})
            return {"error": {"code": "EMBEDDING_FAILED", "message": "Failed to generate embeddings."}}

        dimension = len(valid_vectors[0])

        # 3. Vector Store Add
        np_vectors = np.array(valid_vectors, dtype=np.float32)
        try:
            vector_store.add(np_vectors, valid_metadata, dimension)
            vector_store.save()
            document_service.update_metadata(document_id, {"index_status": "indexed"})
        except Exception as e:
            logger.error(f"Failed to add to vector store: {e}")
            document_service.update_metadata(document_id, {"index_status": "failed"})
            return {"error": {"code": "INDEXING_FAILED", "message": "Failed to store vectors."}}

        return {
            "document_id": document_id,
            "status": "indexed",
            "chunks_created": len(valid_metadata),
            "embedding_dimension": dimension
        }

indexing_service = IndexingService()
