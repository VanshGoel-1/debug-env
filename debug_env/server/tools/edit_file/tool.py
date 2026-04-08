"""
edit_file tool — validates the request, writes the file, then grades via comparison.

If a *_solution.py canonical reference exists in the workdir, we grade by
line-by-line comparison instead of running pytest (which is fragile in tmp dirs).
Falls back to run_tests when no solution file is present.
"""

import logging
from pathlib import Path

from pydantic import ValidationError

from debug_env.server.grader import grade_by_comparison
from debug_env.server.schemas import EditFileArgs, ToolResult
from debug_env.server.tools.run_tests import run_tests
from debug_env.server.utils import validate_workdir_path

logger = logging.getLogger(__name__)


def edit_file(workdir: str, path: str, content: str) -> ToolResult:
    """
    Overwrite *path* (relative to *workdir*) with *content*, then grade.

    Grading strategy:
      1. Look for ``{stem}_solution.py`` in the same workdir.
      2. If found → compare submitted content to reference line-by-line.
      3. If not found → fall back to running pytest via run_tests().

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
        logger.info(f"File written ({len(args.content)} chars)")
    except OSError as e:
        msg = f"Failed to write '{args.path}': {e}"
        logger.error(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)

    # ── Comparison-based grading ──────────────────────────────────────────────
    stem = Path(args.path).stem
    solution_path = Path(workdir) / f"{stem}_solution.py"

    if solution_path.exists():
        try:
            reference = solution_path.read_text(encoding="utf-8")
            pass_rate = grade_by_comparison(args.content, reference)
            logger.info(f"Comparison grade for '{args.path}': {pass_rate:.4f}")
            return ToolResult(
                pass_rate=pass_rate,
                logs=f"Graded '{args.path}' vs reference: pass_rate={pass_rate:.4f}",
                success=True,
            )
        except OSError as e:
            logger.warning(f"Could not read solution file '{solution_path}': {e} — falling back to tests")

    # ── Fallback: run pytest ──────────────────────────────────────────────────
    logger.info("No solution file found — running tests")
    return run_tests(workdir)
