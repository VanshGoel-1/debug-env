"""
run_tests tool — executes pytest inside the task workdir and returns a ToolResult.
"""

import logging
import re
import subprocess

from debug_env.server.schemas import ToolResult

logger = logging.getLogger(__name__)


def _parse_pass_rate(output: str, returncode: int) -> float:
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    error_match = re.search(r"(\d+) error", output)

    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(error_match.group(1)) if error_match else 0

    total = passed + failed + errors
    if total > 0:
        return passed / total
    return 1.0 if returncode == 0 else 0.0


def run_tests(workdir: str) -> ToolResult:
    """
    Run ``pytest -q --tb=short`` inside *workdir*.

    Args:
        workdir: Absolute path to the task working directory.

    Returns:
        :class:`ToolResult` with ``pass_rate`` and ``logs``.
    """
    logger.info(f"Running tests in: {workdir}")

    try:
        result = subprocess.run(
            ["pytest", "-q", "--tb=short", workdir],
            capture_output=True,
            text=True,
            cwd=workdir,
        )
        output = result.stdout + result.stderr
        pass_rate = _parse_pass_rate(output, result.returncode)

        logger.info(f"Tests complete — pass_rate={pass_rate:.2f} (returncode={result.returncode})")

        return ToolResult(pass_rate=pass_rate, logs=output, success=True)

    except FileNotFoundError:
        msg = "pytest not found. Ensure it is installed in the environment."
        logger.error(msg)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)

    except Exception as e:
        msg = f"Unexpected error running tests: {e}"
        logger.error(msg, exc_info=True)
        return ToolResult(pass_rate=0.0, logs=msg, success=False)
