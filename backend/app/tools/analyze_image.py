from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.tools.base import ToolBase
from app.services.vision_service import vision_service

class AnalyzeImageInput(BaseModel):
    file_path: str = Field(..., description="Absolute path to the image file to analyze.")
    prompt: Optional[str] = Field(None, description="Optional prompt for the vision model to look for specific details.")

class AnalyzeImageOutput(BaseModel):
    vision_id: str
    status: str
    model: str
    analysis: str
    local: bool

class AnalyzeImageTool(ToolBase):
    name: str = "analyze_image"
    description: str = "Analyze an image (PNG, JPG, WEBP) using local Ollama vision capabilities. Useful for inspecting photographs, engineering drawings, or scanned pages."
    InputSchema = AnalyzeImageInput
    OutputSchema = AnalyzeImageOutput

    async def execute(self, input_data: AnalyzeImageInput) -> AnalyzeImageOutput:
        try:
            res = await vision_service.analyze(input_data.file_path, input_data.prompt)
            if "error" in res:
                raise Exception(f"{res['error']['code']}: {res['error']['message']}")
                
            return AnalyzeImageOutput(
                vision_id=res["vision_id"],
                status=res["status"],
                model=res["model"],
                analysis=res["analysis"],
                local=res["local"]
            )
        except Exception as e:
            raise Exception(f"Failed to analyze image: {str(e)}")
