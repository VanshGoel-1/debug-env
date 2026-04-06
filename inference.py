"""
Debug-Env Benchmark Executor (Competition Version)

Evaluates LLM agents on code debugging tasks via the OpenEnv server.
Fully compliant with OpenEnv competition requirements.

Usage:
    python inference.py                        # uses env vars
    TASK=task2 NUMBER_OF_RUNS=3 python inference.py

Required Environment Variables:
    API_BASE_URL        LLM API endpoint (e.g., https://api.openai.com/v1)
    MODEL_NAME          Model identifier (e.g., gpt-4o-mini)
    OPENAI_API_KEY      OpenAI API key

Optional Environment Variables:
    ENV_URL             OpenEnv server URL (default: http://127.0.0.1:8000)
    TASK                task1 | task2 | task3 (default: task1)
    NUMBER_OF_RUNS      how many runs for Pass@k (default: 3)
    MAX_STEPS           max steps per run (default: 40)
    TEMPERATURE         LLM temperature (default: 0.0)
    MAX_TOKENS          max tokens per response (default: 4096)
    REQUEST_DELAY_MS    delay between requests in ms (default: 500)

Output:
    - Structured [START]/[STEP]/[END] logs to stdout
    - Results JSON file: results_{task}_{timestamp}.json
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from math import comb
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

import httpx
from openai import AsyncOpenAI, APIError, RateLimitError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ── Tool definitions for function calling ──────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": (
                "Execute the pytest test suite against the current code. "
                "Returns pass rate and full test output logs."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the current content of a source file in the task working directory. "
                "Use this to inspect broken code and helper files."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Filename to read (e.g. 'broken_code.py')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Overwrite a source file with corrected content and run tests. "
                "Always provide the complete file content (full replacement)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Filename to edit (e.g. 'broken_code.py')",
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete new file content (full file replacement)",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "Fix broken Python code.\n\n"
    "Steps:\n"
    "1. run_tests - see errors\n"
    "2. read_file('broken_code.py') - see buggy code\n"
    "3. edit_file('broken_code.py') - fix it\n"
    "4. run_tests - verify\n\n"
    "Rules:\n"
    "- MUST call edit_file to fix (reading only = reward 0)\n"
    "- Always provide COMPLETE file in edit_file\n"
    "- Stop when all tests pass (reward = 1.0)"
)

# ── Configuration ───────────────────────────────────────────────────────────────

CONFIG = {
    "env_url": os.getenv("ENV_URL", "http://127.0.0.1:8000"),
    "api_base_url": os.getenv("API_BASE_URL", "https://api.openai.com/v1"),
    "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "task": os.getenv("TASK", "task1"),
    "number_of_runs": int(os.getenv("NUMBER_OF_RUNS", "1")),  # Testing: 1 run
    "max_steps_per_run": int(os.getenv("MAX_STEPS", "10")),    # Testing: 10 steps max
    "temperature": float(os.getenv("TEMPERATURE", "0.0")),
    "max_tokens": int(os.getenv("MAX_TOKENS", "1024")),         # Testing: 1K tokens max
    "request_delay_ms": int(os.getenv("REQUEST_DELAY_MS", "500")),
}


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate required environment variables."""
    if not config["openai_api_key"]:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Set it via: export OPENAI_API_KEY=sk-..."
        )
    if not config["model_name"]:
        raise ValueError(
            "MODEL_NAME environment variable is required. "
            "Set it via: export MODEL_NAME=gpt-4o-mini"
        )
    if not config["api_base_url"]:
        raise ValueError(
            "API_BASE_URL environment variable is required. "
            "Set it via: export API_BASE_URL=https://api.openai.com/v1"
        )


# ── OpenAI Client Setup ─────────────────────────────────────────────────────────


async def _init_openai_client(config: Dict[str, Any]) -> AsyncOpenAI:
    """Initialize AsyncOpenAI client with proper configuration."""
    return AsyncOpenAI(
        api_key=config["openai_api_key"],
        base_url=config["api_base_url"],
    )


# ── OpenEnv Environment Client ──────────────────────────────────────────────────


async def env_reset(env_url: str, task: str) -> Dict[str, Any]:
    """Reset the environment to the initial state for a task."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{env_url}/reset", json={"task": task})
        r.raise_for_status()
        return r.json()


async def env_step(
    env_url: str, tool: str, args: Dict[str, Any], delay_ms: int = 500
) -> Dict[str, Any]:
    """Execute a tool step with retry logic and rate limiting."""
    action = {"tool": tool, "args": args}

    # Rate limiting delay
    await asyncio.sleep(delay_ms / 1000.0)

    # Retry logic for transient errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(f"{env_url}/step", json={"action": action})
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Rate limited. Retrying in {wait_time}s (attempt {attempt+1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)
            else:
                raise
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                f"Request failed: {e}. Retrying (attempt {attempt+1}/{max_retries})"
            )
            await asyncio.sleep(1)

    raise RuntimeError(f"Failed to execute {tool} after {max_retries} retries")


# ── Single Run Execution ────────────────────────────────────────────────────────


async def execute_run(
    run_number: int,
    client: AsyncOpenAI,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a single run of the debugging task."""
    from copy import deepcopy

    env_url = config["env_url"]
    task = config["task"]
    max_steps = config["max_steps_per_run"]
    model = config["model_name"]

    # Structured logging: [START]
    print(f"[START] run={run_number} task={task} model={model}")

    # Reset environment
    reset_data = await env_reset(env_url, task)
    initial_logs = (reset_data.get("observation") or {}).get("logs", "")

    # Initialize message history
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"Task: {task}\n\n"
                f"Tests:\n{initial_logs}\n\n"
                f"Fix broken_code.py. Start with run_tests."
            ),
        },
    ]

    rewards: List[float] = []
    tools_used: List[str] = []
    steps_detail: List[Dict] = []
    success = False
    start_ts = datetime.now(timezone.utc)

    for step in range(1, max_steps + 1):
        try:
            # LLM call with function calling
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )

            # Check if LLM finished without tool calls
            assistant_message = response.choices[0].message
            has_tool_calls = hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls

            # Debug: Log what tools the model is trying to call
            if has_tool_calls:
                tool_names = [tc.function.name for tc in assistant_message.tool_calls]
                logger.debug(f"Model trying to call: {tool_names}")

            if not has_tool_calls:
                logger.info("LLM finished reasoning without tool calls")
                break

            # Process tool calls
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in assistant_message.tool_calls
                ] if assistant_message.tool_calls else None
            })

            tool_results = []
            for tc in assistant_message.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                # Execute tool in environment
                res = await env_step(
                    env_url,
                    tool_name,
                    tool_args,
                    delay_ms=config["request_delay_ms"],
                )
                reward = res.get("reward", 0.0)
                done = res.get("done", False)
                logs = (res.get("observation") or {}).get("logs", "")

                rewards.append(reward)
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

                steps_detail.append(
                    {
                        "step": step,
                        "tool": tool_name,
                        "args": {
                            k: v[:120] + "…"
                            if isinstance(v, str) and len(v) > 120
                            else v
                            for k, v in tool_args.items()
                        },
                        "reward": reward,
                        "done": done,
                    }
                )

                # Structured logging: [STEP]
                print(
                    f"[STEP] run={run_number} step={step} "
                    f"tool={tool_name} reward={reward:.2f} done={done}"
                )

                # Add tool result to messages
                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": f"reward={reward}, done={done}\n\n{logs}",
                    }
                )

                if done:
                    success = True
                    break

            # Add all tool results to messages
            messages.extend(tool_results)

            if success:
                break

        except (RateLimitError, APIError) as e:
            logger.error(f"OpenAI API error at step {step}: {e}")
            if step < max_steps:
                await asyncio.sleep(2)
            else:
                break
        except Exception as e:
            logger.error(f"Unexpected error at step {step}: {e}", exc_info=True)
            break

    elapsed_ms = int(
        (datetime.now(timezone.utc) - start_ts).total_seconds() * 1000
    )
    final_reward = rewards[-1] if rewards else 0.0

    # Structured logging: [END]
    print(
        f"[END] run={run_number} success={success} "
        f"steps={len(rewards)} final_reward={final_reward:.2f} elapsed_ms={elapsed_ms}"
    )

    return {
        "run_number": run_number,
        "success": success,
        "final_reward": final_reward,
        "rewards": rewards,
        "steps": steps_detail,
        "tools_used": tools_used,
        "elapsed_ms": elapsed_ms,
    }


# ── Statistics Calculation ──────────────────────────────────────────────────────


def calculate_statistics(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate Pass@k and other metrics from run results."""
    total = len(runs)
    successes = [r for r in runs if r["success"]]
    n_success = len(successes)

    # Pass@k: probability that at least one of k runs succeeds
    pass_at = {}
    for k in range(1, total + 1):
        if total - n_success < k:
            pass_at[f"pass@{k}"] = 1.0
        else:
            pass_at[f"pass@{k}"] = (
                1.0 - comb(total - n_success, k) / comb(total, k)
            )

    avg_steps = sum(len(r["rewards"]) for r in runs) / total if total else 0
    avg_final_reward = sum(r["final_reward"] for r in runs) / total if total else 0
    mean_time_ms = sum(r["elapsed_ms"] for r in runs) / total if total else 0

    # Tool usage across all runs
    tool_counts: Dict[str, int] = {}
    for r in runs:
        for t in r["tools_used"]:
            tool_counts[t] = tool_counts.get(t, 0) + 1

    return {
        "total_runs": total,
        "successful_runs": n_success,
        "success_rate": n_success / total if total else 0.0,
        **pass_at,
        "avg_steps_per_run": round(avg_steps, 2),
        "avg_final_reward": round(avg_final_reward, 4),
        "mean_elapsed_ms": round(mean_time_ms, 0),
        "tool_usage": tool_counts,
    }


# ── Main ────────────────────────────────────────────────────────────────────────


async def main(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main benchmark execution."""
    if config is None:
        config = CONFIG

    # Validate configuration
    try:
        _validate_config(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    task = config["task"]
    n_runs = config["number_of_runs"]

    logger.info("=" * 70)
    logger.info(f"DEBUG-ENV BENCHMARK - OPENAI COMPETITION VERSION")
    logger.info(
        f"task={task}  model={config['model_name']}  "
        f"runs={n_runs}  max_steps={config['max_steps_per_run']}"
    )
    logger.info("=" * 70)

    # Initialize OpenAI client
    client = await _init_openai_client(config)
    all_runs: List[Dict[str, Any]] = []

    # Execute runs
    for run_number in range(1, n_runs + 1):
        try:
            result = await execute_run(run_number, client, config)
            all_runs.append(result)
        except Exception as e:
            logger.error(f"Run {run_number} failed: {e}", exc_info=True)
            all_runs.append(
                {
                    "run_number": run_number,
                    "success": False,
                    "final_reward": 0.0,
                    "rewards": [],
                    "steps": [],
                    "tools_used": [],
                    "elapsed_ms": 0,
                    "error": str(e),
                }
            )

    # Calculate statistics
    stats = calculate_statistics(all_runs)

    output = {
        "benchmark_config": {
            "task": task,
            "model": config["model_name"],
            "api_base_url": config["api_base_url"],
            "number_of_runs": n_runs,
            "max_steps_per_run": config["max_steps_per_run"],
            "temperature": config["temperature"],
        },
        "runs": all_runs,
        "statistics": stats,
    }

    # Save results to JSON file
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = f"results_{task}_{ts}.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Print summary
    print()
    print("=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Task:           {task}")
    print(f"Model:          {config['model_name']}")
    print(f"Runs:           {stats['total_runs']}")
    print(f"Success rate:   {stats['success_rate']:.1%}  ({stats['successful_runs']}/{stats['total_runs']})")
    for k in range(1, n_runs + 1):
        key = f"pass@{k}"
        if key in stats:
            print(f"{key:15} {stats[key]:.1%}")
    print(f"Avg steps:      {stats['avg_steps_per_run']}")
    print(f"Avg reward:     {stats['avg_final_reward']:.4f}")
    print(f"Mean time:      {stats['mean_elapsed_ms']:.0f} ms")
    print(f"Tool usage:     {stats['tool_usage']}")
    print(f"Results file:   {out_file}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    asyncio.run(main())
