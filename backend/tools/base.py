from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

from ..config.logging_config import get_logger

logger = get_logger(__name__)


class ToolResult(BaseModel):
    success: bool = True
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    
    def __init__(self) -> None:
        logger.debug(f"Initializing tool: {self.__class__.__name__}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tool_names(self) -> List[str]:
        return list(self.tools.keys())


registry = ToolRegistry() 