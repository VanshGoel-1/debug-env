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

# debug-env — AI Code Debugging Benchmark

An [OpenEnv](https://github.com/meta-pytorch/OpenEnv) benchmark where LLM agents fix broken Python code.
Agents use four tools to diagnose and repair bugs across 9 tasks of increasing complexity.
Rewards are shaped on test pass rate (0.0–1.0) with efficiency bonuses.

**Live Space**: [vanshgoel1-debug-env.hf.space](https://vanshgoel1-debug-env.hf.space)  
**GitHub**: [VanshGoel-1/debug-env](https://github.com/VanshGoel-1/debug-env)

---

## Environment Description

Real-world code debugging is a core developer skill and a meaningful benchmark for LLM agents.
debug-env places agents inside an isolated working directory containing buggy Python code and
a pytest test suite. The agent must use tools to understand the code, identify the bug, and
write a corrected file — all within a fixed step budget.

The environment models genuine debugging scenarios: syntax errors, logic bugs, multi-file
issues, type errors, code quality problems, and collaborative refactoring tasks. These are
tasks developers do every day.

---

## Action Space

```python
class DebugAction(Action):
    tool: str   # one of: "list_files", "run_tests", "read_file", "edit_file"
    args: dict  # tool-specific arguments (see below)
```

| Tool | Args | Description |
|------|------|-------------|
| `list_files` | `{}` | List all editable source files in the task workdir |
| `run_tests` | `{}` | Run pytest and return pass rate + full output |
| `read_file` | `{"path": "broken_code.py"}` | Read a source file |
| `edit_file` | `{"path": "broken_code.py", "content": "..."}` | Overwrite file, then run tests |

---

## Observation Space

```python
class DebugObservation(Observation):
    pass_rate: float  # fraction of tests passing (0.0–1.0)
    logs: str         # test output, file content, or error message
    reward: float     # shaped reward for this step
    done: bool        # True when all tests pass (pass_rate == 1.0)
```

---

## Reward Function

Defined in `debug_env/server/grader.py`:

```
reward = pass_rate
       − min(max(0, (steps − 3) × 0.01), 0.3)   # step penalty after step 3
       + 0.1  if pass_rate == 1.0                  # completion bonus
       + 0.2 × max(0, 1 − steps/max_steps)         # efficiency bonus on full solve
```

- Partial credit for partial test passage (not sparse)
- Penalises thrashing (many steps without progress)
- Rewards solving quickly

---

## Tasks

| ID | Title | Difficulty | Type | Files |
|----|-------|-----------|------|-------|
| task1 | Fix Syntax Error | Easy | Bug fix | `broken_code.py` |
| task2 | Fix Logic Error | Medium | Bug fix | `broken_code.py` |
| task3 | Fix Multi-file Bug | Hard | Bug fix | `broken_code.py`, `helper.py` |
| task4 | Fix Type Errors | Medium | Type check | `typed_code.py` |
| task5 | Remove Dead Code | Medium | Code quality | `messy_code.py` |
| task6 | Architecture Refactor | Hard | Refactoring | 4 files |
| task7 | Code Review Workflow | Medium | Collaborative | `auth.py` |
| task8 | Cross-team Bug Investigation | Hard | Collaborative | 3 files |
| task9 | Collaborative Refactoring | Hard | Collaborative | 4 files |

Tasks 1–3 cover the mandatory competition range (easy → medium → hard).
Tasks 4–9 provide additional challenge for frontier models.

---

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install

```bash
git clone https://github.com/VanshGoel-1/debug-env
cd debug-env

uv sync
```

### Configure

```bash
cp .env.example .env
# Edit .env and set:
#   HF_TOKEN=hf_...          (required)
#   API_BASE_URL=https://router.huggingface.co/v1
#   MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### Verify

```bash
python verify_setup.py
# Expected: 18 passed, 0 failed
```

---

## Usage

### Start the server

```bash
# Terminal 1
uv run server
# Server runs at http://localhost:8000
```

### Run the benchmark

```bash
# Terminal 2
python inference.py

# Run a specific task
TASK=task2 python inference.py

# Multiple runs for Pass@k
TASK=task1 NUMBER_OF_RUNS=3 python inference.py
```

### Verify the server manually

```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"debug-env"}

curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "task1"}'

curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"tool": "list_files", "args": {}}}'
```

---

## Inference Script

`inference.py` uses the OpenAI client against any OpenAI-compatible endpoint.

**Required environment variables:**

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | HuggingFace / API key |
| `API_BASE_URL` | LLM API endpoint (default: `https://router.huggingface.co/v1`) |
| `MODEL_NAME` | Model identifier (default: `Qwen/Qwen2.5-72B-Instruct`) |

**Competition stdout format:**

```
[START] task=task1 env=debug-env model=Qwen/Qwen2.5-72B-Instruct
[STEP]  step=1 action=list_files() reward=0.00 done=false error=null
[STEP]  step=2 action=run_tests() reward=0.00 done=false error=null
[STEP]  step=3 action=read_file('broken_code.py') reward=0.00 done=false error=null
[STEP]  step=4 action=edit_file('broken_code.py') reward=1.10 done=true error=null
[END]   success=true steps=4 score=1.10 rewards=0.00,0.00,0.00,1.10
```

Results are saved to `results_{task}_{timestamp}.json` with `pass@k`, `success_rate`,
`avg_steps`, and `avg_final_reward`.

---

## Docker

```bash
# Build
docker build -t debug-env .

# Run
docker run -p 8000:8000 debug-env

# With Docker Compose
docker-compose up --build
```

The Dockerfile uses a two-stage build: dependencies are installed in the builder stage
(cache-friendly), source code is copied into the runtime stage. The CMD runs uvicorn
directly against `debug_env.server.app:app`.

---

## Deployment to Hugging Face Spaces

```bash
# Authenticate
huggingface-cli login

# Validate before pushing
openenv validate

# Push
openenv push --repo-id your-username/debug-env
```

The `openenv.yaml` at repo root defines the Space configuration. After push, the Space
auto-builds from `Dockerfile` and exposes:

- `GET /health` — health check
- `POST /reset` — start episode
- `POST /step` — execute tool
- `GET /tasks` — list all tasks
- `POST /mcp` — MCP JSON-RPC interface
- `/web` — interactive web UI
- `/docs` — OpenAPI docs

---

## API Reference

### Core endpoints

```
GET  /health                              → {"status":"healthy","service":"debug-env"}
POST /reset   {"task":"task1"}            → initial observation
POST /step    {"action":{"tool":...}}     → observation, reward, done
GET  /state                               → current episode state
WS   /ws                                  → persistent session (low latency)
```

### Task endpoints

```
GET  /tasks                               → paginated task list
GET  /tasks/{taskId}                      → task metadata
GET  /tasks/{taskId}/files                → editable file list
POST /tasks/{taskId}/episodes             → create episode
GET  /tasks/{taskId}/episodes/{id}        → get episode
PATCH /tasks/{taskId}/episodes/{id}       → update episode status
```

### MCP endpoint

```
POST /mcp   {"jsonrpc":"2.0","method":"initialize","params":{"meta":{"task":"task1"}},"id":1}
POST /mcp   {"jsonrpc":"2.0","method":"tools/list","id":2}
POST /mcp   {"jsonrpc":"2.0","method":"tools/call","params":{"name":"run_tests","arguments":{}},"id":3}
```

---

## Project Structure

```
debug-env/                    ← repo root, all commands run here
├── pyproject.toml            ← single package definition
├── uv.lock                   ← committed lock file
├── Dockerfile                ← single Dockerfile
├── docker-compose.yml
├── openenv.yaml              ← OpenEnv spec
├── inference.py              ← competition entry point
├── train.py                  ← RL training (GRPO)
├── verify_setup.py
└── debug_env/
    ├── models.py             ← DebugAction, DebugObservation
    ├── client.py             ← DebugEnv HTTP/WS client
    ├── server/
    │   ├── app.py            ← FastAPI entry point
    │   ├── debug_env_environment.py
    │   ├── grader.py         ← reward shaping
    │   ├── core/apis.py      ← /health
    │   ├── database/         ← SQLAlchemy + SQLite
    │   ├── handlers/         ← MCP JSON-RPC dispatcher
    │   ├── mcp/              ← MCP router + tool specs
    │   ├── schemas/          ← Pydantic schemas
    │   ├── tasks/            ← registry, loader, API routes
    │   ├── tools/            ← run_tests, read_file, edit_file, list_files
    │   │                       + 6 advanced analysis tools
    │   └── utils/            ← path validation
    ├── rl/
    │   ├── dataset.py        ← curriculum dataset for GRPO
    │   └── rollout.py        ← reward bridge for TRL
    └── tasks/
        ├── task1/ – task3/   ← static broken_code.py + test_code.py
        └── task4/ – task9/   ← seed_data.py (generated at runtime)
```

---

## RL Training (Optional)

GRPO training against the live environment using TRL + Unsloth:

```bash
uv sync --extra training
uv run server          # Terminal 1 — environment must be running
python train.py        # Terminal 2

# Smaller model for low VRAM:
MODEL=Qwen/Qwen2.5-1.5B-Instruct python train.py

# Easy tasks only (recommended starting point):
TASK_FILTER=easy python train.py
```

VRAM reference (Unsloth 4-bit QLoRA):

| Model | Min VRAM |
|-------|---------|
| Qwen2.5-1.5B | ~2 GB |
| Qwen2.5-7B | ~6 GB |
| Qwen2.5-14B | ~10 GB |

---

## License

BSD 3-Clause — see [LICENSE](LICENSE)
