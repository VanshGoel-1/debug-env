import logging
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from debug_env.models import DebugAction, DebugObservation
from debug_env.server.grader import grade
from debug_env.server.schemas import ToolResult
from debug_env.server.tasks import TaskLoader
from debug_env.server.tools import edit_file, read_file, run_tests

logger = logging.getLogger(__name__)


def _make_error_obs(message: str) -> DebugObservation:
    """Return a zero-reward observation for environment-level errors."""
    obs = DebugObservation(pass_rate=0.0, logs=message)
    obs.reward = 0.0
    obs.done = False
    return obs


def _obs_from_result(result: ToolResult) -> DebugObservation:
    """Convert a ToolResult into a DebugObservation with reward and done flag."""
    obs = DebugObservation(pass_rate=result.pass_rate, logs=result.logs)
    obs.reward = grade(result.pass_rate)
    obs.done = result.pass_rate == 1.0
    return obs


class DebugEnvironment(Environment):

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.current_task = "task1"
        self.workdir: str | None = None

    def reset(self, seed: int | None = None, episode_id: str | None = None, task: str | None = None, **kwargs) -> DebugObservation:  # noqa: ARG002
        if task is not None:
            self.current_task = task
        self._state = State(episode_id=episode_id or str(uuid4()), step_count=0)
        self.workdir = TaskLoader.load(self.current_task, self.workdir)
        logger.info(f"Reset — task={self.current_task} workdir={self.workdir}")
        return DebugObservation(
            pass_rate=0.0,
            logs=f"Task '{self.current_task}' loaded. Fix the bugs!",
        )

    # ── Tool dispatch ──────────────────────────────────────────────────────────

    def _handle_run_tests(self, workdir: str) -> ToolResult:
        return run_tests(workdir)

    def _handle_read_file(self, workdir: str, args: dict) -> ToolResult:
        return read_file(workdir, path=args.get("path", ""))

    def _handle_edit_file(self, workdir: str, args: dict) -> ToolResult:
        return edit_file(
            workdir,
            path=args.get("path", ""),
            content=args.get("content", ""),
        )

    # ── Core step ──────────────────────────────────────────────────────────────

    def step(self, action: DebugAction, timeout_s: float | None = None, **kwargs) -> DebugObservation:  # noqa: ARG002
        self._state.step_count += 1

        if self.workdir is None:
            return _make_error_obs("Environment not initialised — call reset first.")

        tool = action.tool
        args = action.args or {}

        logger.info(f"Step {self._state.step_count} — tool={tool}")

        try:
            if tool == "run_tests":
                result = self._handle_run_tests(self.workdir)
            elif tool == "read_file":
                result = self._handle_read_file(self.workdir, args)
            elif tool == "edit_file":
                result = self._handle_edit_file(self.workdir, args)
            else:
                result = ToolResult(
                    pass_rate=0.0,
                    logs=f"Unknown tool: '{tool}'. Use 'run_tests', 'read_file', or 'edit_file'.",
                    success=False,
                )
        except Exception as e:
            logger.error(f"Unexpected error in tool '{tool}': {e}", exc_info=True)
            return _make_error_obs(f"Internal error executing '{tool}'. Contact admin if issue persists.")

        return _obs_from_result(result)

    @property
    def state(self) -> State:
        return self._state
