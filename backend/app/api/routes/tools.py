from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.tools.registry import tool_registry

router = APIRouter()

@router.get("/tools")
async def list_tools():
    return tool_registry.list_tools()

@router.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, input_data: Dict[str, Any]):
    return await tool_registry.execute(tool_name, input_data)
