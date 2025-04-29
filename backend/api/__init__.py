from fastapi import APIRouter

from .routes import router as api_router
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

from .auth_routes import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
router.include_router(api_router)

__all__ = [
    "router",
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "TaskCreate",
    "TaskResponse",
    "TaskListResponse",
    "ErrorResponse",
    "SuccessResponse",
    "AgentListResponse",
    "MemorySearchRequest",
    "MemorySearchResponse"
] 