"""
Episode executor — the bridge between TRL's GRPOTrainer and the debug-env server.

Takes a model-generated text completion, parses tool calls from it, executes
them against the running environment server, and returns a scalar reward.

The server must be running at ENV_URL before any rollout executes:
    uv run server   # or: uvicorn debug_env.server.app:app --port 8000
"""

import asyncio
import json
import re

import httpx

from debug_env.server.grader import grade_with_steps

ENV_URL = "http://127.0.0.1:8000"
MAX_STEPS = 15
REQUEST_DELAY_S = 0.2  # 200 ms between steps to avoid overwhelming the server


# ── Tool-call parser ──────────────────────────────────────────────────────────

def parse_tool_calls(text: str) -> list[dict]:
    """
    Extract tool calls from model-generated text.

    Handles two formats:

    Format 1 — JSON blocks (preferred):
        ```json
        {"tool": "run_tests", "args": {}}
        ```

    Format 2 — Function-style (fallback):
        list_files()
        run_tests()
        read_file("broken_code.py")
        edit_file("broken_code.py", content)  followed by a ```python ... ``` block

    Returns:
        List of {"tool": str, "args": dict} dicts, in order of appearance.
    """
    calls: list[dict] = []

    # Format 1: JSON fenced blocks
    for match in re.finditer(r"```(?:json)?\s*(\{[^`]+\})\s*```", text, re.DOTALL):
        try:
            obj = json.loads(match.group(1))
            if "tool" in obj:
                calls.append({"tool": obj["tool"], "args": obj.get("args", {})})
        except json.JSONDecodeError:
            pass

    if calls:
        return calls

    # Format 2: Function-style (fallback for raw text completions)

    # No-arg tools
    for tool in ["list_files", "run_tests"]:
        if f"{tool}(" in text:
            calls.append({"tool": tool, "args": {}})

    # read_file("path")
    for m in re.finditer(r'read_file\(["\']([^"\']+)["\']\)', text):
        calls.append({"tool": "read_file", "args": {"path": m.group(1)}})

    # edit_file("path", ...) followed by a fenced code block
    edit_match = re.search(
        r'edit_file\(["\']([^"\']+)["\'].*?```(?:python)?\n([\s\S]+?)```',
        text,
        re.DOTALL,
    )
    if edit_match:
        calls.append(
            {
                "tool": "edit_file",
                "args": {"path": edit_match.group(1), "content": edit_match.group(2)},
            }
        )

    return calls


# ── Episode runner ────────────────────────────────────────────────────────────

async def _run_episode(completion: str, task_id: str) -> float:
    """
    Run one full episode asynchronously:
      1. POST /reset to initialise the task
      2. Parse tool calls from the completion text
      3. POST /step for each tool call (up to MAX_STEPS)
      4. Return the shaped reward from grade_with_steps()

    Returns 0.0 on any connectivity / parse failure so GRPO training
    is never interrupted by transient server errors.
    """
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(f"{ENV_URL}/reset", json={"task": task_id})
            r.raise_for_status()
        except Exception:
            return 0.0

        tool_calls = parse_tool_calls(completion)
        if not tool_calls:
            return 0.0

        step_count = 0
        final_reward = 0.0

        for call in tool_calls[:MAX_STEPS]:
            step_count += 1
            await asyncio.sleep(REQUEST_DELAY_S)
            try:
                r = await client.post(
                    f"{ENV_URL}/step",
                    json={"action": {"tool": call["tool"], "args": call["args"]}},
                )
                r.raise_for_status()
                data = r.json()
                pass_rate = (data.get("observation") or {}).get("pass_rate", 0.0)
                final_reward = grade_with_steps(pass_rate, step_count)
                if data.get("done", False):
                    break
            except Exception:
                break

        return final_reward


def run_episode(completion: str, task_id: str) -> float:
    """Synchronous wrapper around _run_episode — called from GRPOTrainer reward_funcs."""
    return asyncio.run(_run_episode(completion, task_id))


# ── GRPOTrainer reward_funcs interface ────────────────────────────────────────

def debug_reward(completions: list[str], task_id: list[str], **kwargs) -> list[float]:
    """
    Reward function for TRL's GRPOTrainer.

    GRPOTrainer calls this once per batch with:
        completions — list of model-generated text strings (one per sample)
        task_id     — dataset column forwarded as a keyword list; one ID per sample

    Returns:
        List of float rewards in [0.0, 1.0], one per completion.
    """
    return [
        run_episode(completion, tid)
        for completion, tid in zip(completions, task_id)
    ]
