from openenv.core.env_server.types import Action, Observation
from pydantic import Field

class DebugAction(Action):
    tool: str = Field(..., description="Tool to use: run_tests, read_file, edit_file")
    args: dict = Field(default_factory=dict, description="Arguments for the tool")

class DebugObservation(Observation):
    pass_rate: float = Field(default=0.0, description="Test pass rate (0 to 1)")
    logs: str = Field(default="", description="Test output logs")