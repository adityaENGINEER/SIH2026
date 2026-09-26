from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.indexing_service import indexing_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.rag_service import rag_service
import numpy as np

router = APIRouter()

class IndexRequest(BaseModel):
    document_id: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, le=20, gt=0)
    document_id: Optional[str] = None
    project_id: Optional[str] = None

@router.post("/knowledge/index")
async def index_document(request: IndexRequest):
    return await indexing_service.index_document(request.document_id)

@router.post("/knowledge/search")
async def search_knowledge(request: SearchRequest):
    allowed_document_ids, scope_error = rag_service.resolve_scope(request.document_id, request.project_id)
    if scope_error:
        return scope_error
    is_available = await embedding_service.verify_availability()
    if not is_available:
        return {"error": {"code": "EMBEDDING_MODEL_UNAVAILABLE", "message": "Embedding model not found."}}
        
    query_vector_list = await embedding_service.embed_text(request.query)
    if not query_vector_list:
        return {"error": {"code": "EMBEDDING_FAILED", "message": "Failed to embed query."}}
        
    query_vector = np.array(query_vector_list, dtype=np.float32)
    
    results = vector_store.search(query_vector, request.top_k, allowed_document_ids)
    
    return {
        "query": request.query,
        "results": results
    }

@router.post("/knowledge/query")
async def rag_query(request: SearchRequest):
    return await rag_service.query(request.query, request.top_k, request.document_id, request.project_id)
