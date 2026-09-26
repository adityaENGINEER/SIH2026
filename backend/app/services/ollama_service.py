import httpx
import logging
from app.core.config import settings
from app.services.security_service import security_service

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.ollama_base_url

    async def check_health(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    return "online"
                return "offline"
        except (httpx.RequestError, httpx.TimeoutException):
            return "offline"

    async def list_models(self) -> list:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                return []
        except (httpx.RequestError, httpx.TimeoutException):
            return []

    @staticmethod
    def resolve_installed_name(model_name: str, installed_names) -> str:
        """Ollama reports untagged models as 'name:latest'; treat 'name' and 'name:latest' as the same model."""
        for candidate in (model_name, f"{model_name}:latest"):
            if candidate in installed_names:
                return candidate
        if model_name.endswith(":latest") and model_name[:-7] in installed_names:
            return model_name[:-7]
        return None

    async def is_model_installed(self, model_name: str) -> bool:
        models = await self.list_models()
        return self.resolve_installed_name(model_name, {m.get("name") for m in models}) is not None

    async def get_model_info(self, model_name: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(f"{self.base_url}/api/show", json={"name": model_name})
                if response.status_code == 200:
                    return response.json()
                return {}
        except (httpx.RequestError, httpx.TimeoutException):
            return {}

    async def generate(self, model: str, prompt: str, timeout: int = 120, temperature: float = 0.7,
                       format: str = None, num_predict: int = None) -> dict:
        logger.info(f"Inference requested for model: {model}")
        if not security_service.record_model_call("generate", model, self.base_url):
            return {"error": {"code": "NON_LOCAL_ENDPOINT_BLOCKED", "message": "Model endpoint is not local; call blocked."}}
        
        # Verify model exists locally first
        if not await self.is_model_installed(model):
            logger.error(f"Inference failed: Model {model} is not installed.")
            return {"error": {"code": "MODEL_NOT_INSTALLED", "message": f"Model {model} is not installed in Ollama."}}
            
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if format:
            payload["format"] = format
        if num_predict:
            payload["options"]["num_predict"] = num_predict
        
        logger.info(f"Inference started on model: {model}")
        try:
            # We use a larger timeout here since inference on local CPU/integrated graphics can take time
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Inference completed on model: {model} (Duration: {data.get('total_duration', 0) / 1e9:.2f}s)")
                    return data
                else:
                    logger.error(f"Inference failed with status {response.status_code}")
                    return {"error": {"code": "OLLAMA_INVALID_RESPONSE", "message": f"Ollama returned status {response.status_code}"}}
                    
        except httpx.TimeoutException:
            logger.error(f"Inference timed out after {timeout} seconds on model: {model}")
            return {"error": {"code": "OLLAMA_TIMEOUT", "message": "Inference request timed out."}}
        except httpx.RequestError as e:
            logger.error(f"Inference failed due to connection error: {str(e)}")
            return {"error": {"code": "OLLAMA_UNAVAILABLE", "message": "Failed to connect to local Ollama service."}}

    async def generate_vision(self, model: str, prompt: str, images: list[str], timeout: int = 120, temperature: float = 0.1) -> dict:
        logger.info(f"Vision inference requested for model: {model}")
        if not security_service.record_model_call("vision", model, self.base_url):
            return {"error": {"code": "NON_LOCAL_ENDPOINT_BLOCKED", "message": "Model endpoint is not local; call blocked."}}
        
        # Verify model exists locally first
        if not await self.is_model_installed(model):
            logger.error(f"Vision inference failed: Model {model} is not installed.")
            return {"error": {"code": "MODEL_NOT_INSTALLED", "message": f"Model {model} is not installed in Ollama."}}
            
        payload = {
            "model": model,
            "prompt": prompt,
            "images": images,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        logger.info(f"Vision inference started on model: {model}")
        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Vision inference completed on model: {model} (Duration: {data.get('total_duration', 0) / 1e9:.2f}s)")
                    return data
                else:
                    logger.error(f"Vision inference failed with status {response.status_code}")
                    return {"error": {"code": "VISION_FAILED", "message": f"Ollama returned status {response.status_code}"}}
                    
        except httpx.TimeoutException:
            logger.error(f"Vision inference timed out after {timeout} seconds on model: {model}")
            return {"error": {"code": "OLLAMA_TIMEOUT", "message": "Vision inference request timed out."}}
        except httpx.RequestError as e:
            logger.error(f"Vision inference failed due to connection error: {str(e)}")
            return {"error": {"code": "OLLAMA_UNAVAILABLE", "message": "Failed to connect to local Ollama service."}}

ollama_service = OllamaService()

