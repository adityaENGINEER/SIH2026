import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def initialize(self):
        raise NotImplementedError
        
    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]):
        raise NotImplementedError
        
    def search(self, query_vector: np.ndarray, top_k: int, document_id: str = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def remove_document(self, document_id: str):
        raise NotImplementedError


class NumPyVectorStore(VectorStore):
    def __init__(self):
        self.store_dir = os.path.join(settings.storage_root, "vector_store")
        self.vectors_path = os.path.join(self.store_dir, "vectors.npy")
        self.metadata_path = os.path.join(self.store_dir, "metadata.json")
        self.manifest_path = os.path.join(self.store_dir, "manifest.json")
        
        self.vectors = None
        self.metadata = []
        self.manifest = {
            "embedding_model": "nomic-embed-text",
            "embedding_dimension": None,
            "metric": "cosine",
            "vector_count": 0,
            "document_count": 0,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    def initialize(self):
        os.makedirs(self.store_dir, exist_ok=True)
        if os.path.exists(self.vectors_path) and os.path.exists(self.metadata_path):
            self.load()
        else:
            logger.info("Initialized empty NumPy Vector Store.")

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        """L2 Normalize vectors for cosine similarity via dot product."""
        norm = np.linalg.norm(v, axis=1, keepdims=True)
        # Avoid division by zero
        norm[norm == 0] = 1e-10
        return v / norm

    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]], embedding_dimension: int):
        if len(vectors) != len(metadata):
            raise ValueError("Vectors and metadata length mismatch")
            
        if self.manifest["embedding_dimension"] is None:
            self.manifest["embedding_dimension"] = embedding_dimension
        elif self.manifest["embedding_dimension"] != embedding_dimension:
            raise ValueError(f"Dimension mismatch. Store is {self.manifest['embedding_dimension']}, got {embedding_dimension}")
            
        vectors = self._normalize(vectors)
        
        if self.vectors is None:
            self.vectors = vectors
        else:
            self.vectors = np.vstack([self.vectors, vectors])
            
        self.metadata.extend(metadata)
        self.manifest["vector_count"] = len(self.metadata)
        
        # update document count
        unique_docs = set(m.get("document_id") for m in self.metadata)
        self.manifest["document_count"] = len(unique_docs)
        self.manifest["updated_at"] = datetime.utcnow().isoformat() + "Z"

    def search(self, query_vector: np.ndarray, top_k: int, allowed_document_ids: List[str] = None) -> List[Dict[str, Any]]:
        if self.vectors is None or len(self.vectors) == 0:
            return []
            
        # Ensure 2D
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
            
        query_vector = self._normalize(query_vector)
        
        # Cosine similarity via dot product
        similarities = np.dot(self.vectors, query_vector.T).flatten()
        
        # If allowed_document_ids is provided, mask out vectors that don't match
        if allowed_document_ids is not None:
            mask = np.array([m.get("document_id") in allowed_document_ids for m in self.metadata])
            similarities[~mask] = -1.0
            
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            # If we applied a mask and exhausted valid matches, stop
            if score == -1.0:
                continue
                
            meta = self.metadata[idx]
            results.append({
                "score": score,
                "chunk_id": meta.get("chunk_id"),
                "document_id": meta.get("document_id"),
                "text": meta.get("text"),
                "source": meta.get("source")
            })
            
        return results

    def save(self):
        os.makedirs(self.store_dir, exist_ok=True)
        if self.vectors is not None:
            np.save(self.vectors_path, self.vectors)
            
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)
            
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved NumPy vector store: {len(self.metadata)} vectors.")

    def load(self):
        try:
            self.vectors = np.load(self.vectors_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest = json.load(f)
            logger.info(f"Loaded NumPy vector store with {len(self.metadata)} vectors.")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            raise

    def remove_document(self, document_id: str):
        if self.vectors is None or len(self.metadata) == 0:
            return
            
        indices_to_keep = [i for i, m in enumerate(self.metadata) if m.get("document_id") != document_id]
        
        if len(indices_to_keep) == len(self.metadata):
            return # nothing removed
            
        self.metadata = [self.metadata[i] for i in indices_to_keep]
        self.vectors = self.vectors[indices_to_keep]
        
        self.manifest["vector_count"] = len(self.metadata)
        unique_docs = set(m.get("document_id") for m in self.metadata)
        self.manifest["document_count"] = len(unique_docs)
        self.manifest["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        self.save()

vector_store = NumPyVectorStore()
