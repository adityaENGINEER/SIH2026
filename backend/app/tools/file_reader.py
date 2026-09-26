import os
from app.tools.base import ToolBase
from pydantic import BaseModel
from app.core.config import settings

class FileReaderTool(ToolBase):
    name = "file_reader"
    description = "Reads text files from the safe SovereignAI storage."
    
    class InputSchema(BaseModel):
        path: str
        
    class OutputSchema(BaseModel):
        path: str
        content: str
        
    async def execute(self, input_data: InputSchema) -> OutputSchema:
        base_path = os.path.abspath(settings.storage_root)
        target_path = os.path.abspath(os.path.join(base_path, input_data.path))
        
        # Path traversal / escape check
        if not target_path.startswith(base_path):
            raise ValueError(f"PATH_NOT_ALLOWED: Path '{input_data.path}' escapes the storage root.")
            
        if not os.path.exists(target_path):
            raise ValueError(f"FILE_NOT_FOUND: '{input_data.path}' does not exist.")
            
        if not os.path.isfile(target_path):
            raise ValueError(f"INVALID_PATH: '{input_data.path}' is not a file.")
            
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.OutputSchema(path=input_data.path, content=content)
        except Exception as e:
            raise ValueError(f"READ_FAILED: Could not read file - {e}")
