from pydantic import BaseModel
from typing import Dict, Any, Type, Optional

class ToolBase:
    name: str
    description: str
    
    class InputSchema(BaseModel):
        pass
        
    class OutputSchema(BaseModel):
        pass

    async def execute(self, input_data: BaseModel) -> BaseModel:
        raise NotImplementedError
