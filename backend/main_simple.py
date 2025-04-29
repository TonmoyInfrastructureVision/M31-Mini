import logging
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings

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

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "M31-Mini Autonomous Agent Framework",
        "version": "0.1.0",
        "status": "running",
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_simple:app",
        host=settings.api.host, 
        port=8001,
        reload=settings.api.debug,
    ) 