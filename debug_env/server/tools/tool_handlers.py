"""
MCP Tool Handlers — Generic dispatcher for debug_env analysis tools.

This module provides a generic handler that dynamically executes MCP tools
based on tool configuration, eliminating per-tool if/elif chains and enabling
scalable tool dispatch.

Pattern inspired by calendar_env's tool_handlers.py generic executor.
"""

import logging
from typing import Dict, Any, Callable

from debug_env.server.tools.advanced_tools import (
    search_code,
    get_file_structure,
    run_type_check,
    get_test_coverage,
    list_directory,
    get_dependencies,
)

logger = logging.getLogger(__name__)

# Mapping of tool names to their implementation functions
# Each function signature: func(workdir: str, **kwargs) -> ToolResult
TOOL_IMPLEMENTATIONS: Dict[str, Callable[[str], Any]] = {
    "search_code": search_code,
    "get_file_structure": get_file_structure,
    "run_type_check": run_type_check,
    "get_test_coverage": get_test_coverage,
    "list_directory": list_directory,
    "get_dependencies": get_dependencies,
}

# Lazy-loaded caches to avoid circular imports
_MCP_TOOLS_LIST = None
_TOOL_HANDLERS = None


def get_mcp_tools_list():
    """Get MCP tool definitions (lazy-loaded to avoid circular imports)."""
    global _MCP_TOOLS_LIST
    if _MCP_TOOLS_LIST is None:
        from debug_env.server.mcp.tools.debug_tools import DEBUG_TOOLS
        _MCP_TOOLS_LIST = DEBUG_TOOLS
    return _MCP_TOOLS_LIST


def get_tool_handlers():
    """Get tool handlers dict (lazy-loaded to avoid circular imports)."""
    global _TOOL_HANDLERS
    if _TOOL_HANDLERS is None:
        tools = get_mcp_tools_list()
        _TOOL_HANDLERS = {tool["name"]: execute_tool_generic for tool in tools}
    return _TOOL_HANDLERS


# Convenience aliases for backward compatibility
def __getattr__(name):
    """Module-level __getattr__ for lazy loading."""
    if name == "MCP_TOOLS_LIST":
        return get_mcp_tools_list()
    elif name == "TOOL_HANDLERS":
        return get_tool_handlers()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


async def execute_tool_generic(
    tool_name: str, arguments: Dict[str, Any], workdir: str
) -> Dict[str, Any]:
    """
    Generic tool executor that dispatches to the appropriate tool function.

    This replaces per-tool handlers and allows any tool to be executed
    by looking up its implementation in TOOL_IMPLEMENTATIONS.

    Args:
        tool_name: Name of the tool (e.g., "search_code")
        arguments: Tool arguments from MCP request
        workdir: Working directory for the episode (task files location)

    Returns:
        Dict with "text" (result or error message) and "isError" (bool)
    """
    try:
        # Find tool implementation
        if tool_name not in TOOL_IMPLEMENTATIONS:
            logger.error(f"Unknown tool: {tool_name}")
            return {
                "text": f"Unknown tool: {tool_name}",
                "isError": True,
            }

        tool_func = TOOL_IMPLEMENTATIONS[tool_name]

        logger.debug(f"Executing tool {tool_name} with arguments: {arguments}")

        # Call the tool function with workdir and arguments
        # Tool functions have signature: func(workdir: str, **kwargs) -> ToolResult
        result = tool_func(workdir, **arguments)

        # Tool functions return ToolResult with 'logs' field containing output
        # Check if result is an error based on logs content
        is_error = "error" in result.logs.lower() or result.logs.startswith("Error")

        return {
            "text": result.logs,
            "isError": is_error,
        }

    except TypeError as e:
        logger.error(f"Missing required argument for {tool_name}: {e}")
        return {
            "text": f"Missing required argument: {e}",
            "isError": True,
        }
    except ValueError as e:
        logger.error(f"Invalid argument for {tool_name}: {e}")
        return {
            "text": f"Invalid argument: {e}",
            "isError": True,
        }
    except Exception as e:
        logger.error(f"Error executing {tool_name}: {e}")
        return {
            "text": f"Tool execution failed: {str(e)}",
            "isError": True,
        }
