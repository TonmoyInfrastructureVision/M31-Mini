import json
import asyncio
from typing import Dict, Any, Optional

from .celery_app import app
from ..config.logging_config import get_logger
from ..agent_core import Agent
from ..memory import memory_manager
from ..tools import initialize_tools

logger = get_logger(__name__)


@app.task(name="initialize_system")
def initialize_system():
    logger.info("Initializing system")
    
    async def _init():
        try:
            # Initialize memory stores
            await memory_manager.initialize()
            
            # Initialize tools
            initialize_tools()
            
            logger.info("System initialization complete")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error initializing system: {str(e)}")
            return {"success": False, "error": str(e)}
    
    return asyncio.run(_init())


@app.task(name="run_agent_task")
def run_agent_task(agent_data: Dict[str, Any], goal: str):
    logger.info(f"Running task for agent {agent_data.get('id', 'unknown')}: {goal}")
    
    async def _run():
        try:
            # Create or load agent
            agent = await Agent.from_dict(agent_data)
            
            # Run the task
            result = await agent.run_task(goal)
            
            return result
        except Exception as e:
            logger.error(f"Error running agent task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_data.get("id"),
                "goal": goal
            }
    
    return asyncio.run(_run())


@app.task(name="cancel_agent_task")
def cancel_agent_task(agent_id: str):
    logger.info(f"Cancelling task for agent {agent_id}")
    
    async def _cancel():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state or not agent_state.get("agent_info"):
                return {"success": False, "error": "Agent not found or no state available"}
            
            # Create agent from state
            agent = await Agent.from_dict(agent_state["agent_info"])
            
            # Cancel the task
            cancelled = await agent.cancel_task()
            
            return {"success": cancelled, "agent_id": agent_id}
        except Exception as e:
            logger.error(f"Error cancelling agent task: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_cancel())


@app.task(name="get_agent_status")
def get_agent_status(agent_id: str):
    logger.info(f"Getting status for agent {agent_id}")
    
    async def _get_status():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state:
                return {"success": False, "error": "Agent not found or no state available"}
            
            return {
                "success": True,
                "agent_id": agent_id,
                "status": agent_state.get("status", "unknown"),
                "current_task": agent_state.get("current_task"),
                "updated_at": agent_state.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_get_status())


@app.task(name="get_agent_task_history")
def get_agent_task_history(agent_id: str, limit: int = 10):
    logger.info(f"Getting task history for agent {agent_id}")
    
    async def _get_history():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state or not agent_state.get("agent_info"):
                return {"success": False, "error": "Agent not found or no state available"}
            
            # Create agent from state
            agent = await Agent.from_dict(agent_state["agent_info"])
            
            # Get task history
            history = await agent.get_task_history(limit=limit)
            
            return {"success": True, "agent_id": agent_id, "history": history}
        except Exception as e:
            logger.error(f"Error getting agent task history: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_get_history())


@app.task(name="delete_agent")
def delete_agent(agent_id: str):
    logger.info(f"Deleting agent {agent_id}")
    
    async def _delete():
        try:
            # Get agent state
            agent_state = await memory_manager.short_term.get_agent_state(agent_id)
            if not agent_state or not agent_state.get("agent_info"):
                return {"success": False, "error": "Agent not found or no state available"}
            
            # Create agent from state
            agent = await Agent.from_dict(agent_state["agent_info"])
            
            # Delete the agent
            success = await agent.delete()
            
            return {"success": success, "agent_id": agent_id}
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}")
            return {"success": False, "error": str(e), "agent_id": agent_id}
    
    return asyncio.run(_delete()) 