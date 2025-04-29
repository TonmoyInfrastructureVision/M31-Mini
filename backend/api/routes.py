from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, status, Query
from celery.result import AsyncResult
import json
import os
import asyncio
import uuid
from datetime import datetime

from .models import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    ErrorResponse,
    SuccessResponse,
    AgentListResponse,
    MemorySearchRequest,
    MemorySearchResponse
)
from ..scheduler import (
    app as celery_app,
    run_agent_task,
    cancel_agent_task,
    get_agent_status,
    get_agent_task_history,
    delete_agent,
    initialize_system
)
from ..memory import memory_manager
from ..agent_core import Agent
from ..config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# --- Agent Management Routes ---

@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def create_agent(agent_data: AgentCreate):
    try:
        workspace_dir = agent_data.workspace_dir or "/workspace"
        
        # Create the agent
        agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            model=agent_data.model,
            workspace_dir=workspace_dir
        )
        
        # Save initial state
        await agent.save_state()
        
        return agent.to_dict()
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get(
    "/agents",
    response_model=AgentListResponse,
    responses={
        500: {"model": ErrorResponse}
    }
)
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    try:
        # This is a placeholder - in a real implementation we would
        # query Redis or a database to list all agents
        # For now we'll just return an empty list
        return {
            "agents": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_agent(agent_id: str):
    try:
        # Get agent state from Redis
        agent_state = await memory_manager.short_term.get_agent_state(agent_id)
        if not agent_state or not agent_state.get("agent_info"):
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found"
            )
        
        return agent_state["agent_info"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent: {str(e)}"
        )


@router.patch(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def update_agent(agent_id: str, agent_data: AgentUpdate):
    try:
        # Get agent state from Redis
        agent_state = await memory_manager.short_term.get_agent_state(agent_id)
        if not agent_state or not agent_state.get("agent_info"):
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found"
            )
        
        # Create agent from state
        agent = await Agent.from_dict(agent_state["agent_info"])
        
        # Update fields
        if agent_data.name is not None:
            agent.name = agent_data.name
        
        if agent_data.description is not None:
            agent.description = agent_data.description
        
        if agent_data.model is not None:
            agent.model = agent_data.model
        
        # Save updated state
        await agent.save_state()
        
        return agent.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete(
    "/agents/{agent_id}",
    response_model=SuccessResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def remove_agent(agent_id: str):
    try:
        # Call delete agent task
        task = delete_agent.delay(agent_id)
        result = task.get(timeout=30)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "Failed to delete agent")
            )
        
        return {
            "success": True,
            "message": f"Agent {agent_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete agent: {str(e)}"
        )


# --- Task Management Routes ---

@router.post(
    "/tasks",
    response_model=TaskResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def create_task(task_data: TaskCreate, background_tasks: BackgroundTasks):
    try:
        agent_id = task_data.agent_id
        goal = task_data.goal
        
        # Get agent state from Redis
        agent_state = await memory_manager.short_term.get_agent_state(agent_id)
        if not agent_state or not agent_state.get("agent_info"):
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found"
            )
        
        # Create the agent object
        agent = await Agent.from_dict(agent_state["agent_info"])
        
        if agent.status != "idle":
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent_id} is already running a task"
            )
        
        # Create a task ID
        task_id = str(uuid.uuid4())
        
        # Create initial task response
        task_response = {
            "id": task_id,
            "agent_id": agent_id,
            "goal": goal,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        # Start task in background
        background_tasks.add_task(
            lambda: run_agent_task.delay(agent.to_dict(), goal)
        )
        
        return task_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_task(task_id: str):
    try:
        # This is a placeholder - in a real implementation we would
        # query Redis or a database to get task details by ID
        # For now, let's return a 404
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task: {str(e)}"
        )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=SuccessResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def cancel_task(task_id: str):
    try:
        # Get the agent ID for this task
        # (In a real implementation, we would query a task store)
        # For this simplified version, let's assume we have the agent ID
        agent_id = "unknown"  # placeholder
        
        # Call cancel task
        task = cancel_agent_task.delay(agent_id)
        result = task.get(timeout=30)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "Failed to cancel task")
            )
        
        return {
            "success": True,
            "message": f"Task {task_id} cancelled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get(
    "/agents/{agent_id}/tasks",
    response_model=TaskListResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def list_agent_tasks(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100),
):
    try:
        # Call get task history task
        task = get_agent_task_history.delay(agent_id, limit)
        result = task.get(timeout=30)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "Failed to get task history")
            )
        
        return {
            "agent_id": agent_id,
            "tasks": result.get("history", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks for agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tasks: {str(e)}"
        )


# --- Memory Management Routes ---

@router.post(
    "/memories/search",
    response_model=MemorySearchResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def search_memories(request: MemorySearchRequest):
    try:
        agent_id = request.agent_id
        query = request.query
        limit = request.limit
        memory_type = request.memory_type
        
        # Search memories
        memories = await memory_manager.search_memory(
            agent_id=agent_id,
            query=query,
            limit=limit,
            search_type=memory_type
        )
        
        return {
            "agent_id": agent_id,
            "memories": memories,
            "query": query
        }
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search memories: {str(e)}"
        )


# --- System Routes ---

@router.post(
    "/system/initialize",
    response_model=SuccessResponse,
    responses={
        500: {"model": ErrorResponse}
    }
)
async def init_system():
    try:
        # Initialize system
        task = initialize_system.delay()
        result = task.get(timeout=60)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize system: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": "System initialized successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize system: {str(e)}"
        ) 