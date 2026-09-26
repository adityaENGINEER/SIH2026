from typing import Dict, Any, List, Optional
from app.tools.base import ToolBase
from app.tools.calculator import CalculatorTool
from app.tools.file_reader import FileReaderTool
from app.tools.file_writer import FileWriterTool
from app.tools.document_reader import DocumentReaderTool
from app.tools.document_generator import DocumentGeneratorTool
from app.tools.sandbox_executor import SandboxTool
from app.tools.analyze_image import AnalyzeImageTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolBase] = {}
        self.register(CalculatorTool())
        self.register(FileReaderTool())
        self.register(FileWriterTool())
        self.register(DocumentReaderTool())
        self.register(DocumentGeneratorTool())
        self.register(SandboxTool())
        self.register(AnalyzeImageTool())

    def register(self, tool: ToolBase):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolBase]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "available": True
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, input_data: dict) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool:
            return {
                "tool": name,
                "status": "failed",
                "error": {
                    "code": "TOOL_NOT_FOUND",
                    "message": f"Tool '{name}' is not registered."
                }
            }

        try:
            # Validate input
            try:
                validated_input = tool.InputSchema(**input_data)
            except Exception as e:
                return {
                    "tool": name,
                    "status": "failed",
                    "error": {
                        "code": "INVALID_TOOL_INPUT",
                        "message": str(e)
                    }
                }
                
            from app.services.security_service import security_service
            from app.core.request_context import current_project_id, current_task_id
            security_service.log_event(
                event_type="tool_execution", source=f"tool:{name}", destination="local",
                allowed=True, reason="local tool execution",
                project_id=current_project_id.get(), task_id=current_task_id.get(), agent_run_id=current_task_id.get(),
            )
            result = await tool.execute(validated_input)
            
            # Validate output is implicitly done by returning the OutputSchema model
            
            return {
                "tool": name,
                "status": "completed",
                "result": result.model_dump()
            }
            
        except Exception as e:
            return {
                "tool": name,
                "status": "failed",
                "error": {
                    "code": "TOOL_EXECUTION_FAILED",
                    "message": str(e)
                }
            }

tool_registry = ToolRegistry()
