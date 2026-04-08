# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Debug Env Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import DebugAction, DebugObservation


class DebugEnv(
    EnvClient[DebugAction, DebugObservation, State]
):
    """
    Client for the Debug Env Environment.

    Maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.

    Example:
        >>> with DebugEnv(base_url="http://localhost:8000") as client:
        ...     client.reset(task="task1")
        ...     result = client.step(DebugAction(tool="run_tests", args={}))
        ...     print(result.observation.pass_rate)

    Example with Docker:
        >>> client = DebugEnv.from_docker_image("debug_env-env:latest")
        >>> try:
        ...     client.reset(task="task1")
        ...     result = client.step(DebugAction(tool="list_files", args={}))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: DebugAction) -> Dict:
        """Convert DebugAction to JSON payload for the step message."""
        return {
            "tool": action.tool,
            "args": action.args,
        }

    def _parse_result(self, payload: Dict) -> StepResult[DebugObservation]:
        """Parse server response into StepResult[DebugObservation]."""
        obs_data = payload.get("observation", {})
        observation = DebugObservation(
            pass_rate=obs_data.get("pass_rate", 0.0),
            logs=obs_data.get("logs", ""),
            done=payload.get("done", False),
            reward=payload.get("reward"),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State object."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
