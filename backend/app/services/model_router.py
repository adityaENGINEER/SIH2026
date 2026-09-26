from typing import Any, Dict, Optional

from app.core.config import settings

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
VISION_KEYWORDS = (
    "analyze this image", "analyze image", "analyze inspection photo", "inspect this photograph",
    "inspect photo", "analyze this drawing", "analyze p&id image", "understand this scanned document",
    "identify visible equipment", "inspect this scanned page", "describe this image", "what is in this image",
)
SCAN_KEYWORDS = ("scanned", "scan ", "ocr")
DOCUMENT_KEYWORDS = ("report", "document", "inspection", "approval", "analyze", "summarize", "extract", "find", "search")


class ModelRouter:
    def __init__(self):
        self.reasoning_model = settings.general_model
        self.vision_model = settings.vision_model
        self.embedding_model = settings.embedding_model

    def select_model(self, task_type: str, modality: str = "text") -> str:
        if modality == "image" or modality == "mixed":
            return self.vision_model
        
        if task_type == "embedding":
            return self.embedding_model
            
        return self.reasoning_model

    @staticmethod
    def is_pdf_document(document_meta: Optional[Dict[str, Any]]) -> bool:
        if not document_meta or "error" in document_meta:
            return False
        filename = (document_meta.get("original_filename") or document_meta.get("filename") or "").lower()
        return (document_meta.get("content_type") or "").lower() == "application/pdf" or filename.endswith(".pdf")

    @staticmethod
    def is_image_document(document_meta: Optional[Dict[str, Any]]) -> bool:
        if not document_meta or "error" in document_meta:
            return False
        content_type = (document_meta.get("content_type") or "").lower()
        filename = (document_meta.get("original_filename") or document_meta.get("filename") or "").lower()
        return content_type.startswith("image/") or filename.endswith(IMAGE_EXTENSIONS)

    def route(self, user_request: str, document_meta: Optional[Dict[str, Any]] = None,
              installed_models: Optional[list] = None) -> Dict[str, Any]:
        """Decides which local model serves a request. Returned dict is persisted and shown in the UI."""
        req = (user_request or "").lower()
        has_image = self.is_image_document(document_meta)
        scanned_pdf = self.is_pdf_document(document_meta) and any(kw in req for kw in SCAN_KEYWORDS)

        if has_image or scanned_pdf or any(kw in req for kw in VISION_KEYWORDS):
            reason = ("image input attached" if has_image
                      else "scanned/OCR request on attached PDF" if scanned_pdf
                      else "vision request detected in prompt")
            if installed_models is not None and not self._installed(self.vision_model, installed_models):
                return {"model": self.reasoning_model, "purpose": "general", "capability": "text",
                        "reason": f"{reason}, but vision model '{self.vision_model}' is not installed"}
            return {"model": self.vision_model, "purpose": "vision", "capability": "image", "reason": reason}

        if document_meta and "error" not in document_meta:
            return {"model": self.reasoning_model, "purpose": "general", "capability": "document_rag",
                    "reason": "document analysis with retrieval (embeddings via " + self.embedding_model + ")"}
        if any(kw in req for kw in DOCUMENT_KEYWORDS):
            return {"model": self.reasoning_model, "purpose": "general", "capability": "document_rag",
                    "reason": "knowledge/document analysis with retrieval (embeddings via " + self.embedding_model + ")"}
        return {"model": self.reasoning_model, "purpose": "general", "capability": "text", "reason": "general text query"}

    @staticmethod
    def _installed(model: str, installed_models: list) -> bool:
        names = {m.get("name", "") if isinstance(m, dict) else str(m) for m in installed_models}
        return model in names or any(n.split(":")[0] == model.split(":")[0] for n in names)

model_router = ModelRouter()
