import httpx
import json
from typing import Dict, List, Any, Optional, Union
import time
import uuid

from ..config.settings import settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class LLMResponse:
    def __init__(
        self,
        content: str,
        model: str,
        usage: Dict[str, int],
        id: str,
    ) -> None:
        self.content = content
        self.model = model
        self.usage = usage
        self.id = id


class LLMWrapper:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.llm.api_key
        self.base_url = settings.llm.base_url
        self.default_model = model or settings.llm.default_model
        self.timeout = settings.llm.timeout
        self.max_tokens = settings.llm.max_tokens
        self.temperature = settings.llm.temperature
        
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        model = model or self.default_model
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://m31mini.com",
            "X-Title": "M31-Mini Agent Framework"
        }
        
        logger.debug(f"Making LLM request to model: {model}")
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                response_data = response.json()
                
                duration = time.time() - start_time
                logger.debug(f"LLM request completed in {duration:.2f}s")
                
                return response_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        response_data = await self._make_request(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        try:
            content = response_data["choices"][0]["message"]["content"]
            model_used = response_data.get("model", self.default_model)
            usage = response_data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            response_id = response_data.get("id", str(uuid.uuid4()))
            
            return LLMResponse(
                content=content,
                model=model_used,
                usage=usage,
                id=response_id,
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            logger.error(f"Response data: {json.dumps(response_data)}")
            raise
    
    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        response_data = await self._make_request(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        
        try:
            content = response_data["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Response data: {json.dumps(response_data)}")
            raise


default_llm = LLMWrapper()