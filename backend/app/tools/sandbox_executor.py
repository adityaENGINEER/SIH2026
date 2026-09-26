from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.tools.base import ToolBase
from app.services.sandbox import sandbox_service

class SandboxInput(BaseModel):
    code: str = Field(..., description="The Python code to execute.")

class SandboxOutput(BaseModel):
    execution_id: str
    status: str
    stdout: str
    stderr: str
    exit_code: int

class SandboxTool(ToolBase):
    name: str = "execute_python_code"
    description: str = "Execute Python code in a secure sandbox and return stdout, stderr, and exit_code."
    InputSchema = SandboxInput
    OutputSchema = SandboxOutput

    async def execute(self, input_data: SandboxInput) -> SandboxOutput:
        try:
            # We run this synchronously for now, or could use asyncio.to_thread
            result = sandbox_service.execute(input_data.code)
            return SandboxOutput(
                execution_id=result.execution_id,
                status=result.status,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code
            )
        except Exception as e:
            raise Exception(f"Failed to execute code: {str(e)}")
