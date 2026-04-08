# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Debug Env Environment.

This module creates an HTTP server that exposes the DebugEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

from openenv.core.env_server.http_server import create_app

from debug_env.models import DebugAction, DebugObservation
from debug_env.server.core.apis import router as core_router
from debug_env.server.database.db import init_db
from debug_env.server.debug_env_environment import DebugEnvironment
from debug_env.server.mcp.router import router as mcp_router
from debug_env.server.tasks.router import router as tasks_router


# Create the app with web interface and README integration
app = create_app(
    DebugEnvironment,
    DebugAction,
    DebugObservation,
    env_name="debug_env",
    max_concurrent_envs=1,  # increase this number to allow more concurrent WebSocket sessions
)

# Register additional routers
app.include_router(core_router)
app.include_router(tasks_router)
app.include_router(mcp_router)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and seed task registry on startup."""
    init_db()

@app.get("/")
async def root():
    """Root endpoint for HF Spaces health checks."""
    return {"status": "ok", "message": "debug-env is running!"}


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m debug_env.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn debug_env.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
