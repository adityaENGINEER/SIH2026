import os
import uuid
import base64
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.ollama_service import ollama_service

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        self.supported_formats = [".png", ".jpg", ".jpeg", ".webp", ".pdf"]
        # History for retrieval
        self.results: Dict[str, Dict[str, Any]] = {}
        
    def validate_image(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            raise ValueError(f"FILE_NOT_FOUND: Image file not found at {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_formats:
            raise ValueError(f"INVALID_FILE_TYPE: Unsupported image format {ext}. Supported formats: {', '.join(self.supported_formats)}")
            
        if os.path.getsize(file_path) == 0:
            raise ValueError("INVALID_FILE_TYPE: Image file is empty")
            
        # Security: Prevent path traversal
        abs_file = os.path.abspath(file_path)
        abs_storage = os.path.abspath(settings.storage_root)
        if not abs_file.startswith(abs_storage):
            raise ValueError("PATH_TRAVERSAL: Image file is outside approved storage.")
            
        return True
        
    def _encode_image(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            import fitz
            doc = fitz.open(file_path)
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
            doc.close()
            return base64.b64encode(img_data).decode("utf-8")
        else:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

    async def analyze(self, file_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        vision_id = f"vision_{uuid.uuid4().hex[:8]}"
        
        try:
            self.validate_image(file_path)
        except ValueError as e:
            return {"error": {"code": str(e).split(":")[0], "message": str(e)}}
            
        structured = not prompt
        if structured:
            prompt = """Analyze this image and return structured JSON containing:
{
  "description": "General description",
  "objects": ["identified object 1", "identified object 2"],
  "observations": ["observation 1"],
  "visible_text": ["text 1"],
  "warnings": ["warning 1"],
  "uncertainties": ["uncertainty 1"]
}
If a field cannot be determined, use "Not determinable from image." for strings, or an empty list for arrays."""

        encoded_img = self._encode_image(file_path)
        
        # Use local ollama vision model
        model = settings.vision_model
        
        # Small vision models return an empty string when a free-form question is forced into JSON,
        # so the JSON instruction only accompanies the built-in structured prompt.
        llm_prompt = prompt + "\n\nCRITICAL: Respond ONLY with valid JSON." if structured else prompt
        
        res = await ollama_service.generate_vision(
            model=model,
            prompt=llm_prompt,
            images=[encoded_img],
            timeout=180, # Hardware awareness (Ryzen 5)
            temperature=0.1
        )
        
        if "error" in res:
            return res # Pass through MODEL_NOT_INSTALLED, OLLAMA_TIMEOUT, etc.
            
        raw_text = res.get("response", "").strip()
        if not raw_text:
            return {"error": {"code": "VISION_EMPTY_RESPONSE", "message": f"Vision model '{model}' returned an empty response."}}
        
        # Try parse JSON
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
        raw_text = raw_text.strip()
        
        try:
            analysis_data = json.loads(raw_text)
            if isinstance(analysis_data, dict):
                # Add safety disclaimer
                analysis_data["safety_warning"] = "AI-generated visual analysis. Human verification required."
                analysis = json.dumps(analysis_data)
            else:
                analysis = raw_text + "\n\nAI-generated visual analysis. Human verification required."
        except Exception:
            analysis = raw_text + "\n\nAI-generated visual analysis. Human verification required."
            
        result = {
            "vision_id": vision_id,
            "status": "completed",
            "model": model,
            "analysis": analysis,
            "local": True
        }
        
        self.results[vision_id] = result
        return result
        
    def get_result(self, vision_id: str) -> Optional[Dict[str, Any]]:
        return self.results.get(vision_id)

vision_service = VisionService()
