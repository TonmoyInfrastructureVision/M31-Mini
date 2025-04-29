from typing import Dict, List, Any, Optional, Tuple, Union
import json
import asyncio
import time
from datetime import datetime

from config.logging_config import get_logger
from tools import execute_tool, registry
from memory import memory_manager
from .llm_wrapper import default_llm, LLMResponse

logger = get_logger(__name__)


class ExecutionResult:
    def __init__(
        self,
        step_id: int,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None,
        tool_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.step_id = step_id
        self.success = success
        self.result = result
        self.error = error
        self.tool_used = tool_used
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "tool_used": self.tool_used,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionResult':
        return cls(
            step_id=data.get("step_id", 0),
            success=data.get("success", False),
            result=data.get("result"),
            error=data.get("error"),
            tool_used=data.get("tool_used"),
            metadata=data.get("metadata", {})
        )


class AgentExecutor:
    def __init__(
        self,
        agent_id: str,
        model: Optional[str] = None,
        max_execution_time: int = 300,  # 5 minutes
    ) -> None:
        self.agent_id = agent_id
        self.llm = default_llm
        self.model = model
        self.max_execution_time = max_execution_time
        self.results: List[ExecutionResult] = []
        self.execution_start: Optional[float] = None
        
        # Event for cancellation
        self._cancel_event = asyncio.Event()
    
    def reset(self) -> None:
        self.results = []
        self.execution_start = None
        self._cancel_event.clear()
    
    def cancel(self) -> None:
        self._cancel_event.set()
    
    async def execute_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.reset()
        self.execution_start = time.time()
        
        try:
            steps = plan.get("steps", [])
            
            for i, step in enumerate(steps):
                # Check for cancellation
                if self._cancel_event.is_set():
                    logger.info(f"Execution of plan for agent {self.agent_id} cancelled")
                    break
                
                # Check execution time limit
                elapsed_time = time.time() - self.execution_start
                if elapsed_time > self.max_execution_time:
                    logger.warning(f"Execution time limit reached for agent {self.agent_id}")
                    break
                
                step_id = step.get("id", i + 1)
                description = step.get("description", f"Step {step_id}")
                tool_name = step.get("tool")
                tool_args = step.get("tool_args", {})
                
                logger.info(f"Executing step {step_id} for agent {self.agent_id}: {description}")
                
                if tool_name:
                    result = await self._execute_tool_step(step_id, tool_name, tool_args)
                else:
                    result = await self._execute_thinking_step(step_id, description, plan)
                
                self.results.append(result)
                
                # Store step result in short-term memory
                await memory_manager.add_memory(
                    agent_id=self.agent_id,
                    text=json.dumps(result.to_dict()),
                    metadata={
                        "type": "step_result",
                        "step_id": step_id,
                        "task_id": plan.get("id"),
                    },
                    memory_type="short_term",
                )
                
                # If step failed, we might want to stop or adapt
                if not result.success:
                    logger.warning(f"Step {step_id} failed for agent {self.agent_id}")
                    # Future enhancement: implement adaptive recovery
            
            logger.info(f"Plan execution completed for agent {self.agent_id}")
            return [result.to_dict() for result in self.results]
            
        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}")
            return [result.to_dict() for result in self.results]
    
    async def _execute_tool_step(
        self,
        step_id: int,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> ExecutionResult:
        try:
            logger.debug(f"Executing tool {tool_name} with args: {tool_args}")
            
            if tool_name not in registry.get_tool_names():
                return ExecutionResult(
                    step_id=step_id,
                    success=False,
                    error=f"Tool '{tool_name}' not found",
                    tool_used=tool_name
                )
            
            tool_result = await execute_tool(tool_name, tool_args)
            
            return ExecutionResult(
                step_id=step_id,
                success=tool_result.success,
                result=tool_result.result,
                error=tool_result.error,
                tool_used=tool_name,
                metadata=tool_result.metadata
            )
        except Exception as e:
            logger.error(f"Error executing tool step: {str(e)}")
            return ExecutionResult(
                step_id=step_id,
                success=False,
                error=f"Tool execution error: {str(e)}",
                tool_used=tool_name
            )
    
    async def _execute_thinking_step(
        self,
        step_id: int,
        description: str,
        plan: Dict[str, Any],
    ) -> ExecutionResult:
        try:
            # For thinking steps, we generate a response from the LLM
            # Get context from previous steps
            context = self._build_thinking_context(step_id, plan)
            
            messages = [
                {"role": "system", "content": "You are an autonomous agent executing a plan. For this step, you need to think and provide an analysis or conclusion based on previous steps."},
                {"role": "user", "content": context}
            ]
            
            response = await self.llm.generate_text(
                messages=messages,
                model=self.model,
            )
            
            return ExecutionResult(
                step_id=step_id,
                success=True,
                result=response.content,
                tool_used=None,
                metadata={"tokens": response.usage}
            )
        except Exception as e:
            logger.error(f"Error executing thinking step: {str(e)}")
            return ExecutionResult(
                step_id=step_id,
                success=False,
                error=f"Thinking step error: {str(e)}",
                tool_used=None
            )
    
    def _build_thinking_context(self, current_step_id: int, plan: Dict[str, Any]) -> str:
        goal = plan.get("goal", "Unknown goal")
        thought = plan.get("thought", "")
        
        context = f"""Goal: {goal}

Initial thought: {thought}

Previous steps and results:
"""
        
        # Add results from previous steps
        for result in self.results:
            step_id = result.step_id
            step_index = next((i for i, s in enumerate(plan["steps"]) if s.get("id") == step_id), None)
            
            if step_index is not None:
                step = plan["steps"][step_index]
                description = step.get("description", f"Step {step_id}")
                
                context += f"\nStep {step_id}: {description}\n"
                context += f"Result: {result.result or 'No result'}\n"
                if result.error:
                    context += f"Error: {result.error}\n"
        
        # Add current step info
        step_index = next((i for i, s in enumerate(plan["steps"]) if s.get("id") == current_step_id), None)
        if step_index is not None:
            step = plan["steps"][step_index]
            description = step.get("description", f"Step {current_step_id}")
            context += f"\nCurrent Step {current_step_id}: {description}\n"
        
        context += "\nPlease think through this step and provide your analysis or conclusion."
        
        return context 