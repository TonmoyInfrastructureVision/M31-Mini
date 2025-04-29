# M31-Mini: Autonomous Agent Framework

M31-Mini is a production-ready fullstack autonomous agent framework designed for real-world use in professional environments.

## Features

- 🧠 **Intelligent Agents**: Create autonomous agents that can think, plan and execute tasks
- 🔧 **Modular Tools**: Extensible tool system (web search, file I/O, shell commands)
- 💾 **Dual Memory System**: Long-term (ChromaDB) and short-term (Redis) memory
- 🔄 **Asynchronous Execution**: Celery-based task processing for scalability
- 🌐 **Modern Web UI**: React-based dashboard for agent creation and management
- 🔌 **API-First Design**: RESTful API for easy integration
- 🐳 **Containerized**: Docker-based setup for easy deployment

## System Architecture

```
┌─────────────────┐       ┌───────────────┐
│    Frontend     │◄─────►│  Backend API  │
│  (React/Next.js)│       │   (FastAPI)   │
└─────────────────┘       └───────┬───────┘
                                 ▲ │
                                 │ ▼
┌─────────────────┐       ┌───────────────┐
│  Vector Memory  │◄─────►│  Agent Core   │◄────┐
│    (ChromaDB)   │       └───────┬───────┘     │
└─────────────────┘               │             │
                                  ▼             │
┌─────────────────┐       ┌───────────────┐    │
│  Cache/Queue    │◄─────►│  Task Queue   │    │
│    (Redis)      │       │   (Celery)    │    │
└─────────────────┘       └───────────────┘    │
                                               │
                          ┌───────────────┐    │
                          │    Tools      │────┘
                          │(Web/Files/CLI)│
                          └───────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Make (optional, for using Makefile commands)
- OpenRouter API Key (for LLM access)
- Serper API Key (for web search tool)

## Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/TonmoyInfrastructureVision/M31-Mini.git
   cd M31-Mini
   ```

2. Create an environment file:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file to add your API keys:
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   ```

4. Build and start the containers:
   ```
   make build
   make up
   ```

5. Initialize the system:
   ```
   make init
   ```

6. Access the UI at http://localhost:3000

## Getting Started for New Developers

If you're new to this project, here's a comprehensive guide to help you understand how M31-Mini works and how to get it running.

### How M31-Mini Works

M31-Mini is an autonomous agent framework that connects large language models (LLMs) with various tools and memory systems to create AI agents that can perform tasks. The system has these key components:

#### 1. Agent Core
The brain of the system that handles:
- Planning: Breaking down complex tasks into steps
- Reasoning: Using LLMs to think through problems
- Execution: Running tools to accomplish tasks
- Memory: Storing and retrieving information

#### 2. Memory System
A dual-memory architecture that mimics human cognition:
- Short-term Memory (Redis): Fast, temporary storage for immediate context
- Long-term Memory (ChromaDB): Persistent, searchable knowledge base
- MemoryManager: Orchestrates between both memory types

#### 3. Tools
Modules that give agents capabilities:
- Web search: Finding information online
- File operations: Reading/writing files
- Shell commands: Running system commands
- API calls: Interacting with external services

#### 4. API Layer
FastAPI backend that exposes endpoints for:
- Agent management (create, list, update, delete)
- Task execution and monitoring
- Memory search and management

#### 5. Frontend
React/Next.js application that provides:
- Agent dashboard for creating and managing agents
- Task interface for assigning and monitoring tasks
- Memory explorer for viewing agent knowledge

### Running the Application

#### Option 1: Using Docker (Recommended for Beginners)

This is the easiest way to get started:

1. Install Docker Desktop for your operating system:
   - Windows/Mac: Download from [Docker website](https://www.docker.com/products/docker-desktop)
   - Linux: Follow distro-specific instructions on Docker's website

2. Get API keys:
   - OpenRouter: Sign up at [OpenRouter](https://openrouter.ai/) to access LLMs
   - Serper: Sign up at [Serper.dev](https://serper.dev/) for web search

3. In the M31-Mini directory, copy the example environment file:
   ```bash
   cp env.sample .env
   ```

4. Edit the `.env` file with your API keys and configuration

5. Start the application:
   ```bash
   docker-compose up -d
   ```

6. Access the UI at http://localhost:3000

#### Option 2: Manual Setup (For Development)

If you want to develop or customize the application:

1. Backend Setup:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start Required Services:
   ```bash
   docker-compose up -d redis chromadb
   ```

3. Run the Backend:
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

4. Frontend Setup:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Access the development frontend at http://localhost:3000

### Creating Your First Agent

1. Open the M31-Mini UI at http://localhost:3000
2. Navigate to "Agents" and click "Create Agent"
3. Fill in the details:
   - Name: A descriptive name (e.g., "Research Assistant")
   - Description: The agent's purpose
   - Model: Choose a language model (e.g., GPT-4, Claude)
   - Tools: Select capabilities for your agent

4. Create a task for your agent:
   - Select your agent
   - Enter a task description (e.g., "Research quantum computing basics")
   - Click "Run" and watch your agent work

### Troubleshooting

- **Connection errors**: Ensure all Docker containers are running with `docker ps`
- **API key issues**: Verify your API keys in the `.env` file
- **Memory errors**: Check that Redis and ChromaDB are running properly
- **Frontend not loading**: Ensure the backend API is accessible

### Project Structure

- `/backend`: Python FastAPI application
  - `/agent_core`: Agent logic and execution
  - `/memory`: Dual memory system implementation
  - `/tools`: Tool definitions and implementations
  - `/api`: API endpoints and routing

- `/frontend`: React/Next.js application
  - `/src/pages`: Application pages and routing
  - `/src/components`: UI components
  - `/src/api`: API client for backend communication

## Usage

### Creating an Agent

1. Navigate to the dashboard
2. Click "Create Agent"
3. Enter a name and description
4. Select the AI model (Claude, GPT-4, etc.)
5. Create the agent

### Running a Task

1. Select an agent from the dashboard
2. Enter a task goal in the input field
3. Click "Run Task"
4. View live progress in the task view

## Development

### Backend Development

The backend is built with Python/FastAPI and includes:
- Agent Core: Core agent logic for planning and execution
- Memory System: Dual memory system with vector and cache stores
- Tool System: Modular tools for various capabilities
- Task Processing: Asynchronous task queue with Celery

To run the backend in development mode:

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

The frontend is built with React/Next.js and includes:
- Agent Dashboard: UI for managing agents
- Task View: Real-time task monitoring
- Settings Panel: Configure agents and system

To run the frontend in development mode:

```
cd frontend
npm install
npm run dev
```

## API Reference

The API documentation is available at http://localhost:8000/docs when the server is running.

Key endpoints:

- `POST /api/v1/agents` - Create a new agent
- `GET /api/v1/agents` - List all agents
- `POST /api/v1/tasks` - Create and run a new task
- `GET /api/v1/agents/{agent_id}/tasks` - Get task history

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 