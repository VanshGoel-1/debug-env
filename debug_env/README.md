# debug_env — Python Package

This directory is the `debug_env` Python package. See the [root README](../README.md) for full documentation.

## Package Contents

| Module | Description |
|--------|-------------|
| `models.py` | `DebugAction`, `DebugObservation` Pydantic models |
| `client.py` | `DebugEnv` HTTP/WebSocket client |
| `server/` | FastAPI server — the benchmark environment |
| `tasks/` | Task source files (task1–task9) |
| `rl/` | GRPO training utilities (dataset, rollout) |

## Quick usage

```python
from debug_env import DebugAction, DebugObservation
from debug_env.client import DebugEnvClient

client = DebugEnvClient(base_url="http://localhost:8000")
obs = client.reset(task="task1")
result = client.step(DebugAction(tool="list_files", args={}))
```

## Running the server

```bash
# From repo root
uv run server
```

Server exposes `GET /health`, `POST /reset`, `POST /step`, `GET /tasks`, `POST /mcp`, `/web`, `/docs`.
