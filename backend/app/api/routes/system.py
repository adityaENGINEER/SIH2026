from fastapi import APIRouter
from app.services.ollama_service import ollama_service
from app.services.model_registry import model_registry

router = APIRouter()

@router.get("/system/status")
async def system_status():
    ollama_status = await ollama_service.check_health()
    
    response = {
        "backend": "online",
        "ollama": ollama_status,
        "environment": "local"
    }
    
    if ollama_status == "online":
        response["models"] = await model_registry.get_registry_status()
        
    return response
