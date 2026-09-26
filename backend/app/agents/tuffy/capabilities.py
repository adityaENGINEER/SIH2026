from typing import Dict, Any
from app.services.rag_service import rag_service
from app.tools.registry import tool_registry

class KnowledgeSearchCapability:
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query")
        document_id = input_data.get("document_id")
        project_id = input_data.get("project_id")
        
        if not query:
            return {"error": "Missing query in input data"}
            
        if "top_k" in input_data:
            return await rag_service.query(query_text=query, top_k=int(input_data["top_k"]), document_id=document_id, project_id=project_id)
        return await rag_service.query(query_text=query, document_id=document_id, project_id=project_id)

class ToolExecutionCapability:
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = input_data.get("tool_name")
        tool_input = input_data.get("tool_input", {})
        
        if not tool_name:
            return {"error": "Missing tool_name in input data"}
            
        return await tool_registry.execute(tool_name, tool_input)

# Registry for capabilities
capabilities_registry = {
    "knowledge_search": KnowledgeSearchCapability(),
    "tool_execution": ToolExecutionCapability()
}
