from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import json
import asyncio
import uuid
from datetime import datetime

from .planner import AgentPlanner
from .executor import AgentExecutor
from ..memory import memory_manager
from ..tools import registry
from ..config.logging_config import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class Agent:
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        model: Optional[str] = None,
        id: Optional[str] = None,
        workspace_dir: str = "/workspace",
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description or f"Agent {name}"
        self.model = model or settings.llm.default_model
        self.workspace_dir = workspace_dir
        self.created_at = datetime.now().isoformat()
        self.status = "idle"
        self.current_task: Optional[Dict[str, Any]] = None
        
        # Core components
        self.planner = AgentPlanner(agent_id=self.id, model=self.model)
        self.executor = AgentExecutor(agent_id=self.id, model=self.model)
        
        # Event for task completion
        self._task_complete = asyncio.Event()
        
        # Callback registry
        self._callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_step_complete": [],
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "status": self.status,
            "created_at": self.created_at,
            "workspace_dir": self.workspace_dir,
            "current_task": self.current_task
        }
    
    @classmethod
    async def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        agent = cls(
            name=data.get("name", "Unnamed Agent"),
            description=data.get("description"),
            model=data.get("model"),
            id=data.get("id"),
            workspace_dir=data.get("workspace_dir", "/workspace")
        )
        
        # Restore state if this is an existing agent
        if data.get("id"):
            state = await memory_manager.short_term.get_agent_state(data["id"])
            if state:
                agent.status = state.get("status", "idle")
                agent.current_task = state.get("current_task")
        
        return agent
    
    async def save_state(self) -> None:
        state = {
            "agent_info": self.to_dict(),
            "status": self.status,
            "current_task": self.current_task,
            "updated_at": datetime.now().isoformat()
        }
        
        await memory_manager.store_agent_state(self.id, state)
        logger.debug(f"Saved state for agent {self.id}")
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for event {event_type}: {str(e)}")
    
    async def run_task(self, goal: str) -> Dict[str, Any]:
        if self.status != "idle":
            logger.warning(f"Agent {self.id} is already running a task")
            return {
                "success": False,
                "error": "Agent is already running a task",
                "agent_id": self.id
            }
        
        self.status = "running"
        self._task_complete.clear()
        
        # Create task record
        task_id = str(uuid.uuid4())
        self.current_task = {
            "id": task_id,
            "goal": goal,
            "status": "planning",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "results": []
        }
        
        await self.save_state()
        
        # Trigger task start callbacks
        self._trigger_callbacks("on_task_start", {"agent": self.to_dict(), "task": self.current_task})
        
        try:
            # Get available tools for context
            available_tools = registry.list_tools()
            
            # Retrieve relevant memories
            context = await memory_manager.get_agent_context(
                agent_id=self.id,
                query=goal,
                max_short_term=5,
                max_long_term=3
            )
            
            # Add tools to context
            context["available_tools"] = available_tools
            
            # Create plan
            self.current_task["status"] = "planning"
            await self.save_state()
            
            plan = await self.planner.create_plan(goal, context)
            
            # Store the plan in task record
            self.current_task["plan"] = plan
            self.current_task["status"] = "executing"
            await self.save_state()
            
            # Execute the plan
            logger.info(f"Executing plan for goal: {goal}")
            results = await self.executor.execute_plan(plan)
            
            # Store results
            self.current_task["results"] = results
            
            # Create a reflection on the task
            self.current_task["status"] = "reflecting"
            await self.save_state()
            
            reflection = await self.planner.reflect_on_task(goal, plan, results, context)
            
            # Complete the task
            self.current_task["reflection"] = reflection
            self.current_task["status"] = "completed"
            self.current_task["completed_at"] = datetime.now().isoformat()
            self.status = "idle"
            
            # Trigger task complete callbacks
            self._trigger_callbacks("on_task_complete", {
                "agent": self.to_dict(),
                "task": self.current_task,
                "success": True
            })
            
            await self.save_state()
            self._task_complete.set()
            
            return {
                "success": True,
                "task_id": task_id,
                "goal": goal,
                "plan": plan,
                "results": results,
                "reflection": reflection,
                "agent_id": self.id
            }
            
        except Exception as e:
            logger.error(f"Error executing task for agent {self.id}: {str(e)}")
            
            self.current_task["status"] = "failed"
            self.current_task["error"] = str(e)
            self.status = "idle"
            
            # Trigger task complete callbacks with failure
            self._trigger_callbacks("on_task_complete", {
                "agent": self.to_dict(),
                "task": self.current_task,
                "success": False,
                "error": str(e)
            })
            
            await self.save_state()
            self._task_complete.set()
            
            return {
                "success": False,
                "error": str(e),
                "task_id": self.current_task.get("id"),
                "goal": goal,
                "agent_id": self.id
            }
    
    async def cancel_task(self) -> bool:
        if self.status != "running":
            return False
        
        # Cancel execution
        self.executor.cancel()
        
        # Update task status
        if self.current_task:
            self.current_task["status"] = "cancelled"
            self.current_task["cancelled_at"] = datetime.now().isoformat()
        
        self.status = "idle"
        await self.save_state()
        
        return True
    
    async def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        memories = await memory_manager.search_memory(
            agent_id=self.id,
            query="type:plan",
            limit=limit,
            search_type="long_term"
        )
        
        tasks = []
        for memory in memories:
            try:
                plan_data = json.loads(memory["text"])
                
                # Try to get reflection for this plan
                reflection_memories = await memory_manager.search_memory(
                    agent_id=self.id,
                    query=f"type:reflection goal:{plan_data.get('goal', '')}",
                    limit=1,
                    search_type="long_term"
                )
                
                reflection = None
                if reflection_memories:
                    try:
                        reflection = json.loads(reflection_memories[0]["text"])
                    except json.JSONDecodeError:
                        pass
                
                task = {
                    "id": plan_data.get("id", memory["id"]),
                    "goal": plan_data.get("goal", "Unknown goal"),
                    "created_at": memory["metadata"].get("timestamp"),
                    "status": "completed" if reflection else "unknown",
                    "success": reflection.get("success", False) if reflection else False
                }
                
                tasks.append(task)
                
            except json.JSONDecodeError:
                logger.warning(f"Could not parse plan data for memory {memory['id']}")
        
        return tasks
    
    async def delete(self) -> bool:
        try:
            await memory_manager.delete_agent_memories(self.id)
            logger.info(f"Deleted agent {self.id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting agent {self.id}: {str(e)}")
            return False 