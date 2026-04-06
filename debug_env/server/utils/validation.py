"""
Common validation utilities shared across tool handlers.
"""

import os


def validate_workdir_path(workdir: str, path: str) -> str:
    """
    Resolve *path* against *workdir* and verify it stays inside the workdir.

    Args:
        workdir: Absolute path to the task working directory.
        path:    Relative filename from the agent (e.g. ``"broken_code.py"``).

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If the resolved path escapes the workdir boundary.
    """
    resolved = os.path.realpath(os.path.join(workdir, path))
    workdir_real = os.path.realpath(workdir)

    if not resolved.startswith(workdir_real + os.sep) and resolved != workdir_real:
        raise ValueError(
            f"Path '{path}' resolves outside the task workdir — access denied."
        )

    return resolved
