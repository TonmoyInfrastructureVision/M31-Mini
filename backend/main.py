import logging
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging.config

from config.settings import settings
from config.logging_config import setup_logging
from api import api_router
from tools import initialize_tools
from memory import memory_manager

# Setup logging
logging_config = setup_logging()
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="M31-Mini Autonomous Agent Framework",
    description="A modular autonomous agent framework for real-world use",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting M31-Mini API")
    
    try:
        # Initialize memory stores
        await memory_manager.initialize()
        logger.info("Memory stores initialized")
        
        # Initialize tools
        initialize_tools()
        logger.info("Tools initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down M31-Mini API")
    
    try:
        # Close memory stores
        await memory_manager.close()
        logger.info("Memory stores closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "M31-Mini Autonomous Agent Framework",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
    ) 