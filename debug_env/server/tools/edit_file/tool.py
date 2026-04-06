"""
edit_file tool — validates the request, writes the file, then re-runs tests.
"""

import logging

from pydantic import ValidationError

from debug_env.server.schemas import EditFileArgs, ToolResult
from debug_env.server.tools.run_tests import run_tests
from debug_env.server.utils import validate_workdir_path

logger = logging.getLogger(__name__)


def edit_file(workdir: str, path: str, content: str) -> ToolResult:
    """
    Overwrite *path* (relative to *workdir*) with *content*, then run tests.

    Args:
        workdir:  Absolute path to the task working directory.
        path:     Filename to edit, e.g. ``"broken_code.py"`` or ``"helper.py"``.
        content:  Complete new file content.

    Returns:
        :class:`ToolResult` with ``pass_rate`` and ``logs``.
    """
    try:
        args = EditFileArgs(path=path, content=content)
    except ValidationError as e:
        messages = [f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
        msg = "Invalid edit_file args — " + "; ".join(messages)
        logger.warning(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)

    try:
        full_path = validate_workdir_path(workdir, args.path)
    except ValueError as e:
        logger.warning(str(e))
        return ToolResult(pass_rate=0.0, logs=str(e), success=False)

    logger.info(f"Editing file: {full_path}")

    try:
        with open(full_path, "w") as f:
            f.write(args.content)
        logger.info(f"File written ({len(args.content)} chars) — running tests")
    except OSError as e:
        msg = f"Failed to write '{args.path}': {e}"
        logger.error(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)

    return run_tests(workdir)
