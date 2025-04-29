# M31-Mini Backend

## Overview
This is the backend service for the M31-Mini Autonomous Agent Framework. It is built with FastAPI and provides the API, task scheduling, memory management, and agent core functionalities.

## Setup

### Prerequisites
- Python 3.11
- pip
- Docker (optional, for containerized deployment)

### Local Development
1. Install Python dependencies:
```bash
bash install_dependencies.sh
```
2. Run the backend server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Using Docker
Build and run the backend service using Docker:
```bash
docker build -t m31-mini-backend .
docker run -p 8000:8000 m31-mini-backend
```

## Project Structure
- `main.py`: FastAPI application entry point
- `agent_core/`: Core agent logic
- `api/`: API routes and authentication
- `memory/`: Memory management modules
- `scheduler/`: Task scheduling with Celery
- `tools/`: Utility tools and helpers
- `config/`: Configuration and logging setup

## Testing
Tests are located in the `tests/` directory.

## Notes
- The backend depends on Redis and ChromaDB services for caching and vector storage.
- Environment variables can be set in the `.env` file.
