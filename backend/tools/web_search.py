import httpx
import json
from typing import Dict, Any, List, Optional
import os

from .base import BaseTool, ToolResult
from ..config.logging_config import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information"
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (max 10)",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.environ.get("SERPER_API_KEY")
        if not self.api_key:
            logger.warning("SERPER_API_KEY not set - web search tool will not work")
    
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        if not self.api_key:
            return ToolResult(
                success=False,
                error="Search API key not configured",
                result="Unable to perform web search: API key missing"
            )
        
        try:
            num_results = min(max(1, num_results), 10)  # Ensure between 1 and 10
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": num_results
            }
            
            logger.debug(f"Performing web search for: {query}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                organic_results = data.get("organic", [])
                
                if not organic_results:
                    return ToolResult(
                        success=True,
                        result="No search results found",
                        metadata={"query": query, "total_results": 0}
                    )
                
                formatted_results = []
                for idx, result in enumerate(organic_results[:num_results], 1):
                    title = result.get("title", "No title")
                    link = result.get("link", "")
                    snippet = result.get("snippet", "No description available")
                    
                    formatted_results.append(
                        f"{idx}. {title}\n   URL: {link}\n   {snippet}\n"
                    )
                
                result_text = "\n".join(formatted_results)
                
                return ToolResult(
                    success=True,
                    result=f"Search results for '{query}':\n\n{result_text}",
                    metadata={
                        "query": query,
                        "total_results": len(organic_results),
                        "returned_results": min(len(organic_results), num_results),
                        "results": organic_results[:num_results]
                    }
                )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during web search: {e.response.status_code} - {e.response.text}")
            return ToolResult(
                success=False,
                error=f"Search API error: {e.response.status_code}",
                result=f"Failed to perform web search: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during web search: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Search request error",
                result=f"Failed to perform web search: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during web search: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Unexpected error",
                result=f"Failed to perform web search: {str(e)}"
            ) 