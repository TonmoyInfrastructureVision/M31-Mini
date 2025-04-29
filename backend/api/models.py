from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    model: Optional[str] = None
    workspace_dir: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    model: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    model: str
    status: str
    created_at: str
    workspace_dir: str
    current_task: Optional[Dict[str, Any]] = None


class TaskCreate(BaseModel):
    goal: str = Field(..., min_length=1)
    agent_id: str


class TaskResponse(BaseModel):
    id: str
    agent_id: str
    goal: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None
    reflection: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    agent_id: str
    tasks: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int


class TaskHistoryItem(BaseModel):
    id: str
    goal: str
    created_at: Optional[str] = None
    status: str
    success: bool


class MemorySearchRequest(BaseModel):
    agent_id: str
    query: str
    limit: Optional[int] = 5
    memory_type: Optional[str] = "long_term"


class MemorySearchResponse(BaseModel):
    agent_id: str
    memories: List[Dict[str, Any]]
    query: str 