from fastapi import APIRouter
from pydantic import BaseModel
from app.services.model_registry import model_registry
from app.services.ollama_service import ollama_service

router = APIRouter()

class GenerateRequest(BaseModel):
    model: str
    prompt: str

@router.get("/models")
async def get_models():
    models_list = await model_registry.get_all_models_detailed()
    return {"models": models_list}

@router.post("/models/generate")
async def generate_model(request: GenerateRequest):
    result = await ollama_service.generate(model=request.model, prompt=request.prompt)
    if "error" in result:
        # We could raise an HTTPException, but the prompt says to return structured errors
        return result
    
    return {
        "model": result.get("model", request.model),
        "response": result.get("response", ""),
        "done": result.get("done", True)
    }
