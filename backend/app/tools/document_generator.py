import os
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from app.tools.base import ToolBase
from app.services.document_generator import document_generator_service
from app.services.evidence_extractor import build_document_data, source_document_chunks

class DocumentGeneratorInput(BaseModel):
    task_id: str = Field(..., description="The ID of the task this document is for.")
    document_data: Optional[Dict[str, Any]] = Field(default=None, description="Structured JSON data for the document following the expected schema.")
    knowledge_context: Optional[str] = Field(default=None, description="Grounded analysis text from the knowledge search step.")
    evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="Retrieved source chunks (text + source reference) from the knowledge search step.")

class DocumentGeneratorOutput(BaseModel):
    file_path: str
    status: str
    message: str
    output: Optional[Dict[str, Any]] = None
    grounding: Optional[Dict[str, Any]] = None

class DocumentGeneratorTool(ToolBase):
    name: str = "generate_approval_document"
    description: str = "Generates a realistic industrial approval / authorization DOCX document based on structured AI analysis data."
    InputSchema = DocumentGeneratorInput
    OutputSchema = DocumentGeneratorOutput

    async def execute(self, input_data: DocumentGeneratorInput) -> DocumentGeneratorOutput:
        grounding = None
        doc_data = input_data.document_data or {}
        if not doc_data:
            evidence = input_data.evidence or []
            if not evidence and input_data.knowledge_context:
                evidence = [{"text": input_data.knowledge_context, "filename": "knowledge search answer", "chunk_id": None}]
            if not evidence:
                raise Exception("No grounded evidence or document data supplied; refusing to generate an ungrounded document.")
            doc_ids = list(dict.fromkeys(e["document_id"] for e in evidence if e.get("document_id")))
            built = await build_document_data(input_data.task_id, evidence,
                                              document_chunks=source_document_chunks(doc_ids))
            doc_data, grounding = built["data"], built["grounding"]

        try:
            file_path = document_generator_service.generate_approval_document(input_data.task_id, doc_data)
        except Exception as e:
            raise Exception(f"Failed to generate document: {str(e)}")

        filename = os.path.basename(file_path)
        return DocumentGeneratorOutput(
            file_path=file_path,
            status="success",
            message=f"Document generated successfully at {file_path}",
            output={"type": "docx", "filename": filename, "path": file_path},
            grounding=grounding,
        )
