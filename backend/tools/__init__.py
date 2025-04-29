from typing import Dict, List, Any, Optional
import logging

from tools.base import registry, BaseTool, ToolResult
from tools.web_search import WebSearchTool
from tools.file_io import FileIOTool
from tools.shell_tool import ShellTool
from config.settings import settings

logger = logging.getLogger(__name__)


def initialize_tools() -> None:
    """Initialize and register all available tools based on configuration."""
    logger.info("Initializing tools")
    
    # Register tools
    registry.register(WebSearchTool())
    registry.register(FileIOTool())
    registry.register(ShellTool())
    
    logger.info(f"Registered {len(registry.tools)} tools: {', '.join(registry.get_tool_names())}")


async def execute_tool(
    tool_name: str, 
    tool_args: Dict[str, Any]
) -> ToolResult:
    """Execute a tool by name with the provided arguments."""
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