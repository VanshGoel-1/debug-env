#!/bin/bash
set -e

echo "Starting OpenEnv server..."
uvicorn debug_env.server.app:app --host 0.0.0.0 --port 7860 2>&1 &
UVICORN_PID=$!

echo "Waiting for server to be ready..."
MAX_WAIT=60
WAITED=0
until curl -sf http://127.0.0.1:7860/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "ERROR: Server failed to start within ${MAX_WAIT}s — aborting"
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo "  waited ${WAITED}s..."
done
echo "Server ready after ${WAITED}s"

python inference.py

# Keep container alive so HF Space stays in Running state
wait $UVICORN_PID
