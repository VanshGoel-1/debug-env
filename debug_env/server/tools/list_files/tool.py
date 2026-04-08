from pathlib import Path

from debug_env.server.schemas import ToolResult


def list_files(workdir: str) -> ToolResult:
    """Return the names of all editable source files in the workdir (excludes test files)."""
    p = Path(workdir)
    files = sorted(
        f.name for f in p.iterdir()
        if f.is_file()
        and not f.name.startswith("test_")
        and not f.stem.endswith("_solution")
    )
    listing = "\n".join(files) if files else "(no files found)"
    return ToolResult(pass_rate=0.0, logs=f"Files in workdir:\n{listing}", success=True)