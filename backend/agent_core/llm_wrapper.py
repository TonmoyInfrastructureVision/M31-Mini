import logging
import time
from typing import Dict, List, Optional, Any, Union, Literal
from functools import wraps

import openai
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import settings

logger = logging.getLogger(__name__)

ProviderType = Literal["openai", "anthropic"]
MessageRole = Literal["system", "user", "assistant", "function", "tool"]


class Message:
    def __init__(
        self, 
        role: MessageRole,
        content: str,
        name: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
    ):
        self.role = role
        self.content = content
        self.name = name
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id
        
    def to_dict(self) -> Dict[str, Any]:
        message_dict = {"role": self.role, "content": self.content}
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.tool_calls:
            message_dict["tool_calls"] = self.tool_calls
            
        if self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id
            
        return message_dict


class LLMResponse:
    def __init__(
        self,
        content: str,
        finish_reason: str,
        usage: Dict[str, int],
        raw_response: Any = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ):
        self.content = content
        self.finish_reason = finish_reason
        self.usage = usage
        self.raw_response = raw_response
        self.tool_calls = tool_calls or []


def handle_llm_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise LLMError("Rate limit exceeded. Please try again later.")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMError(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during LLM call: {str(e)}")
            raise LLMError(f"Unexpected error: {str(e)}")
    return wrapper


class LLMError(Exception):
    pass


class LLMWrapper:
    def __init__(self):
        self.provider = settings.llm.provider
        self.model = settings.llm.model
        self.temperature = settings.llm.temperature
        self.timeout = settings.llm.timeout
        
        # Set up clients
        if settings.llm.api_key:
            openai.api_key = settings.llm.api_key
            
        self.anthropic_client = None
        if settings.llm.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.llm.anthropic_api_key)
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError)),
        reraise=True,
    )
    @handle_llm_errors
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider: Optional[ProviderType] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        provider = provider or self.provider
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        
        if provider == "openai":
            return await self._generate_openai(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
                tools=tools,
            )
        elif provider == "anthropic":
            return await self._generate_anthropic(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )
        else:
            raise LLMError(f"Unsupported provider: {provider}")
            
    async def _generate_openai(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: Optional[int],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        formatted_messages = [message.to_dict() for message in messages]
        
        start_time = time.time()
        logger.debug(f"Calling OpenAI API with model {model}")
        
        kwargs = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
            
        if tools:
            kwargs["tools"] = tools
            
        try:
            response = await openai.ChatCompletion.acreate(**kwargs)
            
            elapsed = time.time() - start_time
            logger.debug(f"OpenAI API call completed in {elapsed:.2f}s")
            
            response_message = response.choices[0].message
            content = response_message.content or ""
            
            return LLMResponse(
                content=content,
                finish_reason=response.choices[0].finish_reason,
                usage=response.usage.to_dict(),
                raw_response=response,
                tool_calls=response_message.get("tool_calls", []),
            )
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            raise
            
    async def _generate_anthropic(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: Optional[int],
        model: str,
    ) -> LLMResponse:
        if not self.anthropic_client:
            raise LLMError("Anthropic client not initialized. Set ANTHROPIC_API_KEY.")
            
        # Convert our message format to Anthropic's format
        formatted_messages = []
        for message in messages:
            # Anthropic doesn't support function or tool messages directly
            # We'll convert them to user messages with formatted content
            if message.role in ["function", "tool"]:
                formatted_content = f"{message.role.upper()} {message.name}: {message.content}"
                formatted_messages.append({"role": "user", "content": formatted_content})
            else:
                formatted_messages.append({"role": message.role, "content": message.content})
                
        start_time = time.time()
        logger.debug(f"Calling Anthropic API with model {model}")
        
        kwargs = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
            
        try:
            response = self.anthropic_client.messages.create(**kwargs)
            
            elapsed = time.time() - start_time
            logger.debug(f"Anthropic API call completed in {elapsed:.2f}s")
            
            return LLMResponse(
                content=response.content[0].text,
                finish_reason=response.stop_reason,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                raw_response=response,
            )
        except Exception as e:
            logger.error(f"Error in Anthropic API call: {str(e)}")
            raise


# Create singleton instance
llm = LLMWrapper()