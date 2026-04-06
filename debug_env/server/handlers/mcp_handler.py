"""
MCP (Model Context Protocol) request handler for debug-env.

Implements the MCP JSON-RPC 2024-11-05 protocol, exposing the three debug
tools (run_tests, read_file, edit_file) and six advanced analysis tools to any
MCP-compatible client.

Session model: a single shared DebugEnvironment is used for MCP sessions.
Call 'initialize' to set up a session (optionally passing {"task": "task2"} in
params.meta), then use 'tools/call' to invoke tools across turns.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Request

logger = logging.getLogger(__name__)

# ── MCP tool definitions ───────────────────────────────────────────────────────

MCP_TOOLS = [
    {
        "name": "run_tests",
        "description": """Execute the pytest test suite against the current code.

        Runs all tests in the task working directory and returns detailed results
        including pass rate and full test output logs.

        Response Structure:
          - pass_rate: Float (0.0–1.0) indicating fraction of tests passed
          - logs: Test output including failures, errors, and summary
          - reward: Scalar reward based on pass_rate (0.0 at fail, >0.0 at pass)
          - done: Boolean, true when all tests pass (pass_rate = 1.0)

        Status Codes:
          - 200: Success - Tests executed (may include failures)
          - 500: Internal error running tests
        """,
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_file",
        "description": """Read the current content of a source file in the task working directory.

        Allows inspection of broken code and helper files before deciding what to edit.
        Reading a file does not affect the test pass rate or episode score.

        Required Parameters:
          - path: Filename to read (relative to workdir), e.g. 'broken_code.py'

        Response Structure:
          - pass_rate: 0.0 (reading doesn't affect score)
          - logs: File content prefixed with filename header
          - success: true if file was read successfully

        Status Codes:
          - 200: Success - File read and returned
          - 400: Bad Request - Invalid filename or path traversal attempt
          - 404: Not Found - File does not exist in task
          - 500: Internal error reading file
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Filename to read (e.g. 'broken_code.py', 'helper.py')",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "edit_file",
        "description": """Overwrite a source file with corrected content and run tests.

        Replaces the entire file content and immediately executes the test suite
        to evaluate the fix. Partial writes are not supported—always provide the
        complete file content.

        Required Parameters:
          - path: Filename to edit (e.g. 'broken_code.py')
          - content: Complete new file content (full replacement)

        Response Structure:
          - pass_rate: Float (0.0–1.0) from subsequent test run
          - logs: Test output showing impact of the edit
          - reward: Scalar reward based on new pass_rate
          - done: Boolean, true when all tests pass
          - success: true if file was written and tests executed

        Status Codes:
          - 200: Success - File written and tests executed
          - 400: Bad Request - Invalid filename or path traversal attempt
          - 404: Not Found - File does not exist in task
          - 500: Internal error writing or testing
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Filename to edit (e.g. 'broken_code.py')",
                },
                "content": {
                    "type": "string",
                    "description": "Complete new file content (full file replacement)",
                },
            },
            "required": ["path", "content"],
        },
    },
]

# Advanced debugging tools will be added at runtime (in _handle_tools_list) to avoid circular imports

# ── Shared environment instance ────────────────────────────────────────────────

_env = None  # lazily initialised on first tool call


def _get_env():
    """Return the shared DebugEnvironment, creating it if needed."""
    global _env
    if _env is None:
        from debug_env.server.debug_env_environment import DebugEnvironment
        _env = DebugEnvironment()
    return _env


# ── JSON-RPC helpers ───────────────────────────────────────────────────────────


def _ok(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


# ── Handler ────────────────────────────────────────────────────────────────────


async def handle_mcp_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dispatch an incoming MCP JSON-RPC request to the appropriate handler.

    Returns None for notifications (caller should respond with 204 No Content).
    """
    try:
        body = await request.json()
    except Exception:
        return _error(None, -32700, "Parse error: request body is not valid JSON")

    method: str = body.get("method", "")
    params: Dict[str, Any] = body.get("params") or {}
    request_id = body.get("id")

    # Notifications have no 'id' — we return None so the router sends 204
    if request_id is None:
        logger.debug(f"MCP notification received: {method}")
        return None

    logger.info(f"MCP request: method={method} id={request_id}")

    if method == "initialize":
        return _handle_initialize(request_id, params)

    if method == "tools/list":
        return _handle_tools_list(request_id)

    if method == "tools/call":
        return await _handle_tools_call(request_id, params)

    return _error(request_id, -32601, f"Method not found: {method}")


# ── Method handlers ────────────────────────────────────────────────────────────


def _handle_initialize(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform the MCP handshake and optionally load a task.

    Clients may pass {"meta": {"task": "task2"}} to select a task up front.
    """
    task = (params.get("meta") or {}).get("task")
    env = _get_env()
    env.reset(task=task)
    logger.info(f"MCP session initialised — task={env.current_task}")

    return _ok(request_id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "debug-env", "version": "0.1.0"},
    })


def _handle_tools_list(request_id: Any) -> Dict[str, Any]:
    """Return the list of available debug tools in MCP format."""
    # Add advanced tools on first call (lazy loading to avoid circular imports)
    if len(MCP_TOOLS) == 3:  # Only have the 3 base tools
        from debug_env.server.tools.tool_handlers import get_mcp_tools_list
        advanced_tools = get_mcp_tools_list()
        MCP_TOOLS.extend(advanced_tools)

    return _ok(request_id, {"tools": MCP_TOOLS})


async def _handle_tools_call(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a debug tool via generic dispatcher and return the result as MCP content."""
    from debug_env.models import DebugAction
    from debug_env.server.tools.tool_handlers import get_tool_handlers

    tool_name: str = params.get("name", "")
    tool_args: Dict[str, Any] = params.get("arguments") or {}

    if not tool_name:
        return _error(request_id, -32602, "Invalid params: 'name' is required")

    env = _get_env()
    if env.workdir is None:
        env.reset()

    # Get tool handlers (lazy-loaded to avoid circular imports)
    tool_handlers = get_tool_handlers()

    # Try advanced tools first via generic dispatcher
    if tool_name in tool_handlers:
        try:
            logger.debug(f"Executing advanced tool {tool_name} via generic dispatcher")
            result = await tool_handlers[tool_name](tool_name, tool_args, env.workdir)
            text = result.get("text", "")
            return _ok(request_id, {
                "content": [{"type": "text", "text": text}],
                "isError": result.get("isError", False),
            })
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}", exc_info=True)
            return _error(request_id, -32603, f"Internal error executing tool '{tool_name}'")

    # Fall back to environment tools (run_tests, read_file, edit_file)
    try:
        action = DebugAction(tool=tool_name, args=tool_args)
        obs = env.step(action)
    except Exception as e:
        logger.error(f"MCP tool call failed — tool={tool_name}: {e}", exc_info=True)
        return _error(request_id, -32603, f"Internal error executing tool '{tool_name}'")

    text = (
        f"pass_rate={obs.pass_rate:.2f}  reward={obs.reward:.2f}  done={obs.done}"
        f"\n\n{obs.logs}"
    )
    return _ok(request_id, {
        "content": [{"type": "text", "text": text}],
        "isError": obs.pass_rate == 0.0 and not obs.done,
    })
