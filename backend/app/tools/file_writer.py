import os
from app.tools.base import ToolBase
from pydantic import BaseModel
from app.core.config import settings

class FileWriterTool(ToolBase):
    name = "file_writer"
    description = "Writes raw text content to safe SovereignAI storage directories."
    
    class InputSchema(BaseModel):
        path: str
        content: str
        
    class OutputSchema(BaseModel):
        path: str
        bytes_written: int
        
    async def execute(self, input_data: InputSchema) -> OutputSchema:
        base_path = os.path.abspath(settings.storage_root)
        target_path = os.path.abspath(os.path.join(base_path, input_data.path))
        
        # Path traversal / escape check
        if not target_path.startswith(base_path):
            raise ValueError(f"PATH_NOT_ALLOWED: Path '{input_data.path}' escapes the storage root.")
            
        # Optional: restrict to specific subdirectories if we want to be strict
        # For M10, requirement says "Allowed areas may include ... outputs ... temp ... Do not allow arbitrary filesystem writes"
        # The base check covers SovereignAI storage, which is acceptable.
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(input_data.content)
            
            bytes_written = len(input_data.content.encode('utf-8'))
            return self.OutputSchema(path=input_data.path, bytes_written=bytes_written)
        except Exception as e:
            raise ValueError(f"WRITE_FAILED: Could not write file - {e}")
