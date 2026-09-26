from app.tools.base import ToolBase
from pydantic import BaseModel
from app.services.document_extractor import document_extractor
from app.services.document_service import document_service

class DocumentReaderTool(ToolBase):
    name = "document_reader"
    description = "Reads extracted content from SovereignAI documents."
    
    class InputSchema(BaseModel):
        document_id: str
        
    class OutputSchema(BaseModel):
        document_id: str
        filename: str
        content: str
        content_status: str
        requires_ocr: bool
        
    async def execute(self, input_data: InputSchema) -> OutputSchema:
        meta_result = document_service.get_metadata(input_data.document_id)
        if "error" in meta_result:
            raise ValueError(f"DOCUMENT_NOT_FOUND: {meta_result['error']['message']}")
            
        extract_result = document_extractor.extract(input_data.document_id)
        if "error" in extract_result:
            raise ValueError(f"EXTRACTION_FAILED: {extract_result['error']['message']}")
            
        return self.OutputSchema(
            document_id=input_data.document_id,
            filename=meta_result.get("original_filename", "unknown"),
            content=extract_result.get("text", ""),
            content_status=extract_result.get("content_status", "unknown"),
            requires_ocr=extract_result.get("requires_ocr", False)
        )
