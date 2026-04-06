"""
read_file tool — returns the current content of a file in the task workdir.

Allows the agent to inspect source files before deciding what to edit,
rather than guessing from test error messages alone.
"""

import logging
import os

from pydantic import ValidationError

from debug_env.server.schemas import ReadFileArgs, ToolResult
from debug_env.server.utils import validate_workdir_path

logger = logging.getLogger(__name__)


def read_file(workdir: str, path: str) -> ToolResult:
    """
    Read *path* (relative to *workdir*) and return its content in ``logs``.

    Pass rate is preserved from the last test run — reading a file does not
    affect the score.  The content is returned in ``logs`` so the agent can
    inspect it in the same observation field it already reads.

    Args:
        workdir:  Absolute path to the task working directory.
        path:     Filename to read, e.g. ``"broken_code.py"`` or ``"helper.py"``.

    Returns:
        :class:`ToolResult` with ``pass_rate=0.0`` and file content in ``logs``.
    """
    try:
        args = ReadFileArgs(path=path)
    except ValidationError as e:
        messages = [f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
        msg = "Invalid read_file args — " + "; ".join(messages)
        logger.warning(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)

    try:
        full_path = validate_workdir_path(workdir, args.path)
    except ValueError as e:
        logger.warning(str(e))
        return ToolResult(pass_rate=0.0, logs=str(e), success=False)

    logger.info(f"Reading file: {full_path}")

    if not os.path.exists(full_path):
        available = [f for f in os.listdir(workdir) if f.endswith(".py") and not f.startswith("test_")]
        msg = (
            f"File '{args.path}' not found. "
            f"Editable source files: {available}"
        )
        logger.warning(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)

    try:
        with open(full_path) as f:
            content = f.read()
        logger.info(f"Read {len(content)} chars from '{args.path}'")
        return ToolResult(
            pass_rate=0.0,
            logs=f"# {args.path}\n{content}",
            success=True,
        )
    except OSError as e:
        msg = f"Failed to read '{args.path}': {e}"
        logger.error(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)
