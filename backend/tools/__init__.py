from typing import Dict, List, Any, Optional

from .base import registry, BaseTool, ToolResult
from .web_search import WebSearchTool
from .file_io import FileIOTool
from .shell_tool import ShellTool
from ..config.settings import settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


def initialize_tools(workspace_dir: str = "/workspace") -> None:
    enabled_tools = settings.tools_enabled
    
    logger.info(f"Initializing tools. Enabled tools: {', '.join(enabled_tools)}")
    
    if "web_search" in enabled_tools:
        registry.register(WebSearchTool())
    
    if "file_io" in enabled_tools:
        registry.register(FileIOTool(workspace_dir=workspace_dir))
    
    if "shell" in enabled_tools:
        registry.register(ShellTool(workspace_dir=workspace_dir))
    
    logger.info(f"Registered {len(registry.tools)} tools: {', '.join(registry.get_tool_names())}")


async def execute_tool(
    tool_name: str, 
    tool_args: Dict[str, Any]
) -> ToolResult:
    tool = registry.get_tool(tool_name)
    
    if not tool:
        logger.error(f"Tool not found: {tool_name}")
        return ToolResult(
            success=False,
            error="Tool not found",
            result=f"The tool '{tool_name}' is not available. Available tools: {', '.join(registry.get_tool_names())}"
        )
    
    try:
        logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
        result = await tool.execute(**tool_args)
        logger.debug(f"Tool execution completed: {tool_name}")
        return result
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return ToolResult(
            success=False,
            error=f"Tool execution error",
            result=f"Error executing {tool_name}: {str(e)}"
        ) 