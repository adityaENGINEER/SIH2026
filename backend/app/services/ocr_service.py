import os
import json
import uuid
import logging
import time
from typing import Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from app.core.config import settings
from app.services.document_service import document_service

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # We start with a conservative DPI for CPU usage
        self.dpi = 200
        
    def _is_tesseract_available(self) -> bool:
        if not pytesseract:
            return False
        try:
            # On Windows, sometimes the executable isn't in PATH.
            # Usually it's in C:\Program Files\Tesseract-OCR\tesseract.exe
            # If not in path, pytesseract fails. Let's do a quick check.
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def process(self, document_id: str) -> Dict[str, Any]:
        """
        Process the document and apply OCR if applicable.
        Updates content.json and returns the result.
        """
        logger.info(f"OCR requested for document_id: {document_id}")
        
        meta_result = document_service.get_metadata(document_id)
        if "error" in meta_result:
            return meta_result

        doc_dir = os.path.dirname(meta_result["storage_path"])
        file_path = meta_result["storage_path"]
        ext = meta_result["extension"].lower()
        
        # We will create an OCR result ID
        ocr_id = str(uuid.uuid4())
        
        if not self._is_tesseract_available():
            logger.error("OCR engine is not available on this machine.")
            return {"error": {"code": "OCR_ENGINE_NOT_AVAILABLE", "message": "Tesseract OCR engine is not installed or not in PATH."}}

        start_time = time.time()
        
        result = {
            "ocr_id": ocr_id,
            "document_id": document_id,
            "status": "processing",
            "document_type": ext.strip("."),
            "pages": [],
            "text": ""
        }
        
        try:
            if ext == ".pdf":
                self._process_pdf(file_path, result)
            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]:
                self._process_image(file_path, result)
            else:
                return {"error": {"code": "OCR_INVALID_INPUT", "message": f"Cannot run OCR on {ext} files."}}
                
            result["status"] = "completed"
            
        except Exception as e:
            logger.error(f"OCR failed for {document_id}: {e}")
            return {"error": {"code": "OCR_FAILED", "message": "An error occurred during OCR processing."}}

        duration = time.time() - start_time
        logger.info(f"OCR completed for {document_id} in {duration:.2f}s")
        
        # Save OCR specific result
        ocr_dir = os.path.join(doc_dir, "ocr", ocr_id)
        os.makedirs(ocr_dir, exist_ok=True)
        ocr_result_path = os.path.join(ocr_dir, "result.json")
        try:
            with open(ocr_result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write OCR result for {document_id}: {e}")

        # Merge with content.json safely
        self._update_content_json(doc_dir, result)

        return result

    def _process_pdf(self, file_path: str, result: Dict[str, Any]):
        if not fitz:
            raise RuntimeError("PyMuPDF is not installed")
            
        doc = fitz.open(file_path)
        full_text = []
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Render page to image at specified DPI
            pix = page.get_pixmap(dpi=self.dpi)
            
            # Convert PyMuPDF pixmap to Pillow Image
            if pix.alpha:
                img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
            else:
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
            # Basic preprocessing (grayscale for OCR)
            img = img.convert('L')
            
            # Run OCR
            text = pytesseract.image_to_string(img)
            text = text.strip()
            
            result["pages"].append({
                "page_number": i + 1,
                "text": text
            })
            if text:
                full_text.append(text)
                
            # Free memory
            del img
            del pix
            
        doc.close()
        result["text"] = "\n\n".join(full_text).strip()

    def _process_image(self, file_path: str, result: Dict[str, Any]):
        if not Image:
            raise RuntimeError("Pillow is not installed")
            
        img = Image.open(file_path)
        img = img.convert('L')
        
        text = pytesseract.image_to_string(img)
        text = text.strip()
        
        result["pages"].append({
            "page_number": 1,
            "text": text
        })
        result["text"] = text
        del img

    def _update_content_json(self, doc_dir: str, ocr_result: Dict[str, Any]):
        content_cache_path = os.path.join(doc_dir, "content.json")
        content = {}
        
        if os.path.exists(content_cache_path):
            try:
                with open(content_cache_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
            except Exception:
                pass
                
        # Merge metadata
        content["content_status"] = "ocr_completed"
        content["requires_ocr"] = False
        content["ocr_used"] = True
        content["ocr_engine"] = "tesseract"
        
        # Override text and pages from OCR result
        content["text"] = ocr_result.get("text", "")
        content["pages"] = ocr_result.get("pages", [])
        
        try:
            with open(content_cache_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to update content.json after OCR: {e}")

    def get_result(self, document_id: str, ocr_id: str) -> Dict[str, Any]:
        meta_result = document_service.get_metadata(document_id)
        if "error" in meta_result:
            return meta_result
            
        doc_dir = os.path.dirname(meta_result["storage_path"])
        ocr_result_path = os.path.join(doc_dir, "ocr", ocr_id, "result.json")
        
        if not os.path.exists(ocr_result_path):
            return {"error": {"code": "DOCUMENT_NOT_FOUND", "message": "OCR result not found."}}
            
        try:
            with open(ocr_result_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"error": {"code": "OCR_FAILED", "message": "Failed to read OCR result."}}

ocr_service = OCRService()
