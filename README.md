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
   git clone https://github.com/yourusername/M31-Mini.git
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