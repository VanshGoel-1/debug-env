"""
Pydantic schemas for tool inputs and results.

These are the internal contracts between the environment and the tool layer —
separate from the public OpenEnv Action/Observation API in models.py.
"""

from pydantic import BaseModel, Field, field_validator


class RunTestsArgs(BaseModel):
    """Input schema for the run_tests tool (no arguments required)."""
    pass


class EditFileArgs(BaseModel):
    """Input schema for the edit_file tool."""

    path: str = Field(
        ...,
        description="Filename to edit relative to the workdir, e.g. 'broken_code.py'",
        min_length=1,
    )
    content: str = Field(
        ...,
        description="Complete new file content (partial writes are not supported)",
    )

    @field_validator("path")
    @classmethod
    def no_path_traversal(cls, v: str) -> str:
        """Reject paths that attempt to escape the workdir."""
        if ".." in v or v.startswith("/"):
            raise ValueError(
                f"Invalid path '{v}': absolute paths and '..' are not allowed."
            )
        return v


class ReadFileArgs(BaseModel):
    """Input schema for the read_file tool."""

    path: str = Field(
        ...,
        description="Filename to read relative to the workdir, e.g. 'broken_code.py'",
        min_length=1,
    )

    @field_validator("path")
    @classmethod
    def no_path_traversal(cls, v: str) -> str:
        """Reject paths that attempt to escape the workdir."""
        if ".." in v or v.startswith("/"):
            raise ValueError(
                f"Invalid path '{v}': absolute paths and '..' are not allowed."
            )
        return v


class ToolResult(BaseModel):
    """Result returned by every tool."""

    pass_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of tests that passed (0.0 – 1.0)",
    )
    logs: str = Field(
        default="",
        description="Full pytest output or error message",
    )
    success: bool = Field(
        default=True,
        description="False when the tool itself failed (not the tests)",
    )
