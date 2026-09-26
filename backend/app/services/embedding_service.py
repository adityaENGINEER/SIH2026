import httpx
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = None, ollama_base_url: str = None):
        from app.core.config import settings
        self.model_name = model_name or settings.embedding_model
        self.ollama_base_url = ollama_base_url or settings.ollama_base_url
        self.dimension = None

    async def verify_availability(self) -> bool:
        """
        Check if the required embedding model is installed in Ollama.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name", "").startswith(self.model_name):
                        return True
            return False
        except Exception as e:
            logger.error(f"Failed to check Ollama models: {e}")
            return False

    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string using Ollama local API.
        """
        from app.services.security_service import security_service
        if not security_service.record_model_call("embedding", self.model_name, self.ollama_base_url):
            return None
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": self.model_name,
                    "prompt": text
                }
                response = await client.post(
                    f"{self.ollama_base_url}/api/embeddings", 
                    json=payload, 
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding")
                
                if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                    logger.error("Invalid embedding returned from Ollama")
                    return None
                    
                # Cache the dimension if we haven't yet
                if self.dimension is None:
                    self.dimension = len(embedding)
                    
                return embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts sequentially.
        """
        embeddings = []
        for text in texts:
            emb = await self.embed_text(text)
            if emb:
                embeddings.append(emb)
            else:
                # If one fails, append an empty list or handle it
                # For simplicity, returning what we successfully got
                # Realistically we should probably fail the whole batch, but we'll drop None
                logger.warning("A text chunk failed to embed")
                embeddings.append([])
        return embeddings

embedding_service = EmbeddingService()
