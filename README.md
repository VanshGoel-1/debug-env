---
title: Debug Env - AI Debugging Benchmark
emoji: 🐛
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: true
app_port: 8000
base_path: /web
tags:
  - openenv
  - debugging
  - benchmark
  - ai-agents
---

# Debug Env — Production-Grade AI Debugging Benchmark

A sophisticated debugging benchmark built on [OpenEnv](https://github.com/meta-pytorch/OpenEnv), designed to evaluate AI agents' ability to identify and fix bugs in real-world Python code. Features 9 progressively complex tasks, comprehensive MCP tool support, SQLite persistence, Docker deployment, and Hugging Face integration.

**Live Demo**: [debug-env.hf.space](https://debug-env.hf.space)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
  - [Docker](#docker)
  - [Hugging Face Spaces](#hugging-face-spaces)
- [API Reference](#api-reference)
- [Tasks](#tasks)
- [MCP Tools](#mcp-tools)
- [Database](#database)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Debug Env is a production-ready debugging environment that challenges AI models to locate and fix bugs across various complexity levels. From simple syntax errors to complex multi-file architectural issues, the benchmark provides realistic debugging scenarios with comprehensive tooling for code analysis.

**Built with:**
- FastAPI + Uvicorn (HTTP server)
- SQLAlchemy (ORM) + SQLite (persistence)
- OpenEnv (environment framework)
- MCP Protocol 2024-11-05 (tool interface)
- Docker (containerization)
- Hugging Face (model integration & hosting)

---

## Key Features

| Feature | Details |
|---------|---------|
| **9 Tasks** | From syntax errors to architecture refactoring |
| **9 MCP Tools** | 3 core + 6 advanced analysis tools |
| **Episode Tracking** | Full task lifecycle with status & metrics |
| **Pagination** | Base64 offset tokens + sync tokens |
| **Multi-User Ready** | User-scoped operations, role-based framework |
| **Production Architecture** | FastAPI, SQLAlchemy, SQLite |
| **Generic Tool Dispatch** | Scalable MCP handler pattern |
| **Docker Ready** | Dockerfile + docker-compose.yml included |
| **HF Integration** | Spaces-compatible, model inference ready |
| **Comprehensive Docs** | Google Calendar API v3-style specs |

---

## Quick Start

### Via Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/yourorg/debug-env
cd debug-env

# Build and run with Docker Compose
docker-compose up --build

# Server runs at http://localhost:8000
```

### Via Python (Local Development)

```bash
# Prerequisites: Python 3.10+, uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/yourorg/debug-env
cd debug-env
uv sync

# Initialize database
python -c "from debug_env.server.database.db import init_db; init_db()"

# Run server
uv run server --port 8000
```

### Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Response:
# {"status":"healthy","service":"debug-env"}
```

---

## Installation

### Requirements

- **Python**: 3.10 or higher
- **Docker**: (optional) For containerized deployment
- **Disk Space**: ~500MB (including dependencies)
- **RAM**: 2GB minimum (4GB recommended)

### Option 1: Docker (Recommended for Deployment)

```bash
docker build -t debug-env:latest .
docker run -p 8000:8000 debug-env:latest
```

### Option 2: Local Development

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv sync

# Initialize database
uv run python -c "from debug_env.server.database.db import init_db; init_db()"

# Run development server
uv run server --reload
```

### Option 3: Hugging Face Spaces

Click the "Duplicate" button on the [Hugging Face Space](https://huggingface.co/spaces/yourorg/debug-env) to deploy your own instance.

---

## Usage

### Web Interface

Visit `http://localhost:8000` to access:
- **Dashboard**: Environment state, reset/step UI
- **Task Browser**: View all 9 tasks and their metadata
- **Episode Tracker**: Track task runs and performance

### Python API (Client)

```python
from debug_env import DebugEnvironment, DebugAction

# Create environment
env = DebugEnvironment()

# Select task
obs = env.reset(task="task1")
print(f"Task: {env.current_task}")
print(f"Workdir: {env.workdir}")

# Read a file
obs = env.step(DebugAction(tool="read_file", args={"path": "broken_code.py"}))
print(obs.logs)

# Edit the file
obs = env.step(DebugAction(tool="edit_file", args={
    "path": "broken_code.py",
    "content": "fixed_code_here"
}))

print(f"Pass Rate: {obs.pass_rate}")
print(f"Done: {obs.done}")
print(f"Reward: {obs.reward}")
```

### MCP Interface (Claude, etc.)

```bash
# Initialize connection
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {"meta": {"task": "task1"}},
    "id": 1
  }'

# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
  }'

# Call a tool (search_code)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_code",
      "arguments": {"pattern": "def .*bug", "file_types": "py"}
    },
    "id": 3
  }'
```

### REST API (HTTP)

```bash
# List tasks with pagination
curl "http://localhost:8000/tasks?maxResults=5"

# Get single task
curl "http://localhost:8000/tasks/task1"

# Create episode
curl -X POST "http://localhost:8000/tasks/task1/episodes"

# Update episode status
curl -X PATCH "http://localhost:8000/tasks/task1/episodes/{episode_id}" \
  -H "Content-Type: application/json" \
  -d '{"status": "passed", "pass_rate": 1.0}'
```

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │   Web UI     │  MCP Client  │  REST API    │             │
│  └──────────────┴──────────────┴──────────────┘             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────────────────────────────────────────────┐
│                  FastAPI Server                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ OpenEnv HTTP Server                               │    │
│  │  POST /reset  POST /step  GET /state  WS /ws      │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌──────────────┬────────────┬──────────────────┐         │
│  │ Core APIs    │ Task APIs  │ MCP Router       │         │
│  │ /health      │ /tasks     │ POST /mcp        │         │
│  └──────────────┴────────────┴──────────────────┘         │
└─────────┬──────────────────────────────────┬────────────────┘
          │                                  │
     ┌────▼──────────────────┐       ┌──────▼──────────┐
     │   DebugEnvironment     │       │  Database Layer │
     │  ├─ reset(task)        │       │  ├─ TaskManager │
     │  ├─ step(action)       │       │  ├─ Models      │
     │  └─ TaskLoader         │       │  └─ Schemas     │
     └────────┬───────────────┘       └──────┬──────────┘
              │                              │
         ┌────▼──────────────┐       ┌──────▼──────────┐
         │  Tool Execution   │       │    SQLite DB    │
         │  ├─ run_tests     │       │  ├─ Tasks       │
         │  ├─ read_file     │       │  ├─ Episodes    │
         │  ├─ edit_file     │       │  └─ Channels    │
         │  ├─ search_code   │       └─────────────────┘
         │  ├─ get_coverage  │
         │  └─ (6 more)      │
         └───────────────────┘
```

### Directory Structure

```
debug-env/
├── debug_env/
│   ├── __init__.py
│   ├── models.py                    # DebugAction, DebugObservation
│   ├── client.py                    # DebugEnv client class
│   │
│   ├── server/
│   │   ├── app.py                   # FastAPI app creation
│   │   ├── debug_env_environment.py # Core DebugEnvironment
│   │   ├── grader.py                # Reward calculation
│   │   │
│   │   ├── core/
│   │   │   └── apis.py              # Health check endpoint
│   │   │
│   │   ├── database/                # NEW: Database layer
│   │   │   ├── db.py                # SQLAlchemy setup
│   │   │   ├── models/
│   │   │   │   └── task.py          # ORM models
│   │   │   └── managers/
│   │   │       └── task_manager.py  # TaskManager class
│   │   │
│   │   ├── handlers/
│   │   │   └── mcp_handler.py       # MCP JSON-RPC dispatcher
│   │   │
│   │   ├── mcp/
│   │   │   ├── router.py            # MCP endpoint
│   │   │   └── tools/
│   │   │       └── debug_tools.py   # Tool definitions
│   │   │
│   │   ├── schemas/
│   │   │   ├── tool_schemas.py      # Tool I/O schemas
│   │   │   └── task_schemas.py      # Task/Episode schemas
│   │   │
│   │   ├── tasks/
│   │   │   ├── data.py              # Task registry
│   │   │   ├── loader.py            # File staging
│   │   │   └── router.py            # Task endpoints
│   │   │
│   │   ├── tools/
│   │   │   ├── advanced_tools.py    # 6 analysis tools
│   │   │   ├── tool_handlers.py     # Generic dispatcher
│   │   │   ├── run_tests/
│   │   │   ├── read_file/
│   │   │   └── edit_file/
│   │   │
│   │   └── utils/
│   │       └── validation.py        # Security checks
│   │
│   ├── tasks/                       # Task seed data
│   │   ├── task1/ → task9/          # 9 tasks
│   │   └── [seed_data.py files]
│   │
│   └── data/
│       └── multi_user_sample.py     # User/role models
│
├── tests/                           # Test suite
│   ├── test_tasks.py
│   ├── test_tools.py
│   └── test_database.py
│
├── Dockerfile                       # Container definition
├── docker-compose.yml               # Multi-container setup
├── pyproject.toml                   # Dependencies
├── README.md                        # This file
├── LICENSE                          # BSD license
└── debug_env.db                     # SQLite database (created)
```

---

## Deployment

### Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Initialize database
RUN python -c "from debug_env.server.database.db import init_db; init_db()"

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "-m", "debug_env.server.app"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  debug-env:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./debug_env:/app/debug_env
      - ./debug_env.db:/app/debug_env.db
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - debug-env
```

#### Build and Deploy

```bash
# Build image
docker build -t debug-env:v1.0.0 .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/debug_env.db:/app/debug_env.db \
  debug-env:v1.0.0

# With Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f debug-env
```

### Hugging Face Spaces

#### Setup

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Choose **"Docker"** as the SDK
4. Configure:
   - **Owner**: Your organization
   - **Space name**: `debug-env`
   - **Visibility**: Public (for demo) or Private (for testing)
   - **Persistent Storage**: Enable (for SQLite DB)
   - **Hardware**: CPU (free) or GPU

#### Configuration

Create `app_config.json`:

```json
{
  "title": "Debug Env Benchmark",
  "description": "AI Debugging Benchmark",
  "emoji": "🐛",
  "colorFrom": "blue",
  "colorTo": "indigo",
  "sdk": "docker",
  "app_port": 8000,
  "base_path": "/web",
  "persistentStorage": {
    "enabled": true,
    "mountPath": "/app/data"
  },
  "tags": ["openenv", "debugging", "benchmark"]
}
```

#### Deploy

```bash
# Push to Hugging Face
git push https://huggingface.co/spaces/yourorg/debug-env main

# Spaces automatically builds and deploys
# Access at: https://yourorg-debug-env.hf.space
```

#### Integration with HF Hub

```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="yourorg/debug-env",
    token="hf_xxxxx"
)

# Make inference calls
result = client.post(
    json={"task": "task1", "tool": "search_code", "pattern": "bug"}
)
```

---

## API Reference

### REST Endpoints

#### Health Check
```
GET /health
Response: {"status": "healthy", "service": "debug-env"}
```

#### Task Management

```
GET /tasks?maxResults=50&pageToken=<token>&syncToken=<token>
Response: {
  "etag": "...",
  "items": [{id, title, description, files, tools, ...}],
  "nextPageToken": "...",
  "nextSyncToken": "..."
}

GET /tasks/{taskId}
Response: {id, title, description, difficulty, bug_type, files, tools, ...}

GET /tasks/{taskId}/files
Response: ["broken_code.py", "helper.py"]

GET /tasks/{taskId}/files/{filename}
Response: {task_id, filename, content}
```

#### Episode Management

```
POST /tasks/{taskId}/episodes
Response: {id, task_id, status: "active", workdir, etag, created_at, ...}

GET /tasks/{taskId}/episodes?maxResults=50&pageToken=<token>
Response: {items: [...], nextPageToken: "..."}

GET /tasks/{taskId}/episodes/{episodeId}
Response: {id, task_id, status, pass_rate, workdir, etag, ...}

PATCH /tasks/{taskId}/episodes/{episodeId}
Body: {status?: "passed"|"failed"|"abandoned", pass_rate?: 0.0-1.0}
Response: {id, task_id, status, pass_rate, ...}
```

### MCP Tools

#### Core Tools (3)

**1. `run_tests`** — Execute pytest suite
```json
{"name": "run_tests", "inputSchema": {"type": "object", "properties": {}}}
```
Returns: `pass_rate` (0.0-1.0), `logs`, `reward`, `done`

**2. `read_file`** — Read file from workdir
```json
{
  "name": "read_file",
  "inputSchema": {
    "type": "object",
    "properties": {"path": {"type": "string"}},
    "required": ["path"]
  }
}
```
Returns: `logs` (file content), `success`

**3. `edit_file`** — Write and test file
```json
{
  "name": "edit_file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {"type": "string"},
      "content": {"type": "string"}
    },
    "required": ["path", "content"]
  }
}
```
Returns: `pass_rate`, `logs`, `reward`, `done`

#### Advanced Tools (6)

**4. `search_code`** — Pattern matching with ripgrep
```json
{
  "name": "search_code",
  "inputSchema": {
    "properties": {
      "pattern": {"type": "string", "minLength": 1, "maxLength": 500},
      "file_types": {"enum": ["py", "all", "txt", "json", "md"]},
      "max_results": {"type": "integer", "minimum": 1, "maximum": 500}
    },
    "required": ["pattern"]
  }
}
```

**5. `get_file_structure`** — AST-based code structure
**6. `run_type_check`** — Mypy static analysis
**7. `get_test_coverage`** — Coverage.py metrics
**8. `list_directory`** — Recursive directory listing
**9. `get_dependencies`** — Import analysis

---

## Tasks

| # | Task | Difficulty | Type | Description |
|---|------|-----------|------|-------------|
| 1 | Syntax Error | Easy | Bug Fix | Fix Python syntax preventing import |
| 2 | Logic Error | Medium | Bug Fix | Fix boolean expression logic |
| 3 | Multi-file Bug | Hard | Bug Fix | Fix bug across multiple modules |
| 4 | Type Errors | Medium | Type Check | Fix mypy type annotation errors |
| 5 | Code Quality | Medium | Cleanup | Remove unused imports/dead code |
| 6 | Architecture | Hard | Refactoring | Multi-file refactoring with circular imports |
| 7 | Code Review | Medium | Collab | Junior submits, senior reviews |
| 8 | Bug Investigation | Hard | Collab | QA reports, team investigates |
| 9 | Team Refactoring | Hard | Collab | Multi-user architecture fix |

---

## Database

### Schema

**task_records** — Task metadata (seeded from registry)
```sql
CREATE TABLE task_records (
  id TEXT PRIMARY KEY,
  title TEXT, description TEXT,
  difficulty TEXT, bug_type TEXT,
  files JSON, tools JSON,
  scenario_type TEXT, participants JSON,
  etag TEXT, created_at DATETIME, updated_at DATETIME
)
```

**episode_records** — Task runs (user episodes)
```sql
CREATE TABLE episode_records (
  id TEXT PRIMARY KEY,
  task_id TEXT, user_id TEXT,
  workdir TEXT, status TEXT,
  pass_rate REAL,
  etag TEXT, created_at DATETIME, updated_at DATETIME
)
```

**watch_channels** — Webhook subscriptions
```sql
CREATE TABLE watch_channels (
  id TEXT PRIMARY KEY,
  task_id TEXT, user_id TEXT,
  webhook_address TEXT, webhook_token TEXT,
  expires_at DATETIME, is_active BOOLEAN,
  created_at DATETIME
)
```

---

## Development

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=debug_env

# Specific test file
pytest tests/test_tasks.py -v
```

### Code Quality

```bash
# Format with Black
black debug_env tests

# Lint with Ruff
ruff check debug_env tests

# Type check with Mypy
mypy debug_env
```

### Adding Tasks

1. Create `debug_env/tasks/taskN/seed_data.py`
2. Register in `server/tasks/data.py`
3. Add to `server/tasks/loader.py`
4. Update `pyproject.toml`

### Adding Tools

1. Implement in `server/tools/advanced_tools.py`
2. Add spec to `server/mcp/tools/debug_tools.py`
3. Update `tool_handlers.py`

---

## Contributing

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/xyz`
3. **Make changes** with tests
4. **Run tests**: `pytest`
5. **Submit PR** with description

---

## License

BSD 3-Clause License — See [LICENSE](LICENSE) file

---

## Citation

```bibtex
@software{debug_env_2026,
  title={Debug Env: Production-Grade AI Debugging Benchmark},
  author={Your Organization},
  year={2026},
  url={https://github.com/yourorg/debug-env}
}
```

---

## Links

- **GitHub**: https://github.com/yourorg/debug-env
- **OpenEnv**: https://github.com/meta-pytorch/OpenEnv
- **Hugging Face**: https://huggingface.co/spaces/yourorg/debug-env
- **Issues**: https://github.com/yourorg/debug-env/issues

---

**Last Updated**: April 3, 2026
