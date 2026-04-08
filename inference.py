"""
Debug-Env Benchmark Executor (Competition Version)

Evaluates LLM agents on code debugging tasks via the OpenEnv server.
Uses the OpenAI client pointed at Hugging Face's OpenAI-compatible router.

Usage:
    python inference.py                        # task1, 1 run
    TASK=task2 NUMBER_OF_RUNS=3 python inference.py

Required Environment Variables:
    HF_TOKEN            Hugging Face API key
    API_BASE_URL        LLM API endpoint (default: https://router.huggingface.co/v1)
    MODEL_NAME          Model identifier  (default: Qwen/Qwen2.5-72B-Instruct)

Optional Environment Variables:
    ENV_URL             OpenEnv server URL   (default: http://127.0.0.1:8000)
    TASK                task1–task3          (default: task1)
    NUMBER_OF_RUNS      runs for Pass@k      (default: 1)
    MAX_STEPS           max steps per run    (default: 10)
    TEMPERATURE         LLM temperature      (default: 0.0)
    MAX_TOKENS          max tokens per call  (default: 2048)
    REQUEST_DELAY_MS    ms between requests  (default: 500)

Output:
    - Structured [START]/[STEP]/[END] logs to stdout
    - results_{task}_{timestamp}.json  (written after every run, not just at end)
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from math import comb
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

import httpx
from openai import OpenAI, APIError, RateLimitError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────────

def _ensure_env_vars():
    """Ensure environment variables exist so os.environ[...] doesn't raise KeyError locally."""
    if "API_BASE_URL" not in os.environ:
        os.environ["API_BASE_URL"] = "https://router.huggingface.co/v1"
    if "MODEL_NAME" not in os.environ:
        os.environ["MODEL_NAME"] = "Qwen/Qwen2.5-72B-Instruct"
    if "API_KEY" not in os.environ:
        os.environ["API_KEY"] = os.environ.get("HF_TOKEN", "dummy_key_for_local_testing")

def get_config() -> Dict[str, Any]:
    _ensure_env_vars()
    return {
        "env_url":           os.getenv("ENV_URL",           "http://localhost:7860"),
        "api_base_url":      os.environ["API_BASE_URL"],
        "model_name":        os.environ["MODEL_NAME"],
        "api_key":           os.environ["API_KEY"],
        "task":              os.getenv("TASK",              "task1"),
        "number_of_runs":    int(os.getenv("NUMBER_OF_RUNS",    "1")),
        "max_steps_per_run": int(os.getenv("MAX_STEPS",         "10")),
        "temperature":       float(os.getenv("TEMPERATURE",     "0.0")),
        "max_tokens":        int(os.getenv("MAX_TOKENS",        "2048")),
        "request_delay_ms":  int(os.getenv("REQUEST_DELAY_MS",  "500")),
    }


def _validate_config(config: Dict[str, Any]) -> None:
    if not config["api_key"]:
        raise ValueError("API_KEY or HF_TOKEN is required.")
    if not config["model_name"]:
        raise ValueError("MODEL_NAME is required.")
    if not config["api_base_url"]:
        raise ValueError("API_BASE_URL is required.")


# ── LLM client (OpenAI SDK → HuggingFace router) ────────────────────────────────

def _init_client() -> OpenAI:
    """OpenAI client pointed at the HuggingFace OpenAI-compatible endpoint."""
    _ensure_env_vars()
    return OpenAI(
        base_url=os.environ["API_BASE_URL"],
        api_key=os.environ["API_KEY"],
    )


# ── OpenEnv HTTP helpers ─────────────────────────────────────────────────────────

async def env_reset(env_url: str, task: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{env_url}/reset", json={"task": task})
        r.raise_for_status()
        return r.json()


async def env_step(
    env_url: str, tool: str, args: Dict[str, Any], delay_ms: int = 500
) -> Dict[str, Any]:
    """Execute one tool step with rate-limiting delay and retry on transient errors."""
    action = {"tool": tool, "args": args}
    await asyncio.sleep(delay_ms / 1000.0)

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(f"{env_url}/step", json={"action": action})
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = 2 ** attempt
                logger.warning(f"Rate limited — retrying in {wait}s")
                await asyncio.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt == 2:
                raise
            logger.warning(f"Request failed: {e} — retrying")
            await asyncio.sleep(1)

    raise RuntimeError(f"Failed to execute {tool} after 3 retries")


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _log_step(step, tool_name, tool_args, reward, done, error=None):
    """Emit competition-format [STEP] line."""
    if tool_args:
        args_str = ", ".join(
            f"'{v}'" if isinstance(v, str) and len(v) <= 40
            else f"'{v[:40]}...'" if isinstance(v, str)
            else str(v)
            for v in tool_args.values()
        )
        action_str = f"{tool_name}({args_str})"
    else:
        action_str = f"{tool_name}()"
    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}", flush=True)


def _parse_file_list(logs: str) -> List[str]:
    """Extract .py filenames from list_files output."""
    return [
        line.strip() for line in logs.splitlines()
        if line.strip().endswith(".py") and not line.strip().startswith("#")
    ]


def _extract_code(raw: str) -> str:
    """
    Extract Python code from an LLM response.
    Handles:
      - Raw code (no fences)
      - ```python ... ``` fences
      - ``` ... ``` fences
    Returns the cleaned code string.
    """
    raw = raw.strip()

    # Try to extract from a code fence
    fence_match = re.search(r'```(?:python)?\n(.*?)```', raw, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # Strip leading/trailing fence markers if present without newline
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first line (``` or ```python) and last ``` line
        inner = lines[1:] if len(lines) > 1 else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        return "\n".join(inner).strip()

    return raw


# ── Single run ───────────────────────────────────────────────────────────────────

async def execute_run(
    run_number: int,
    client: OpenAI,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Single-shot debugging workflow per run:
      1. list_files  — discover editable files (solution files hidden by server)
      2. run_tests   — see initial failures
      3. read_file   — read each source file
      4. LLM call    — ask for fixed code (one call per file, raw Python output)
      5. edit_file   — submit fix; server grades via line-by-line comparison
    No retry loop — one shot per run.
    """
    env_url = config["env_url"]
    task    = config["task"]
    model   = config["model_name"]

    print(f"[START] task={task} env=debug-env model={model}", flush=True)

    rewards:      List[float] = []
    tools_used:   List[str]   = []
    steps_detail: List[Dict]  = []
    success      = False
    global_step  = 0
    start_ts     = datetime.now(timezone.utc)

    def _record(tool_name, tool_args, reward, done):
        nonlocal global_step, success
        global_step += 1
        rewards.append(reward)
        if tool_name not in tools_used:
            tools_used.append(tool_name)
        steps_detail.append({
            "step": global_step, "tool": tool_name,
            "args": tool_args, "reward": reward, "done": done,
        })
        _log_step(global_step, tool_name, tool_args, reward, done)
        if done:
            success = True

    async def _call(tool_name, tool_args=None):
        return await env_step(env_url, tool_name, tool_args or {}, delay_ms=config["request_delay_ms"])

    # ── Reset ──────────────────────────────────────────────────────────────────
    await env_reset(env_url, task)

    # ── Step 1: list_files ─────────────────────────────────────────────────────
    res = await _call("list_files")
    reward, done = res.get("reward", 0.0), res.get("done", False)
    file_list_logs = (res.get("observation") or {}).get("logs", "")
    _record("list_files", {}, reward, done)

    files = _parse_file_list(file_list_logs)
    if not files:
        logger.warning("list_files returned no .py files — falling back to broken_code.py")
        files = ["broken_code.py"]

    # ── Step 2: run_tests (initial) ────────────────────────────────────────────
    if not success:
        res = await _call("run_tests")
        reward, done = res.get("reward", 0.0), res.get("done", False)
        test_logs = (res.get("observation") or {}).get("logs", "")
        _record("run_tests", {}, reward, done)
    else:
        test_logs = ""

    # ── Step 3: read every source file ────────────────────────────────────────
    file_contents: Dict[str, str] = {}
    for f in files:
        if success:
            break
        res = await _call("read_file", {"path": f})
        reward, done = res.get("reward", 0.0), res.get("done", False)
        content = (res.get("observation") or {}).get("logs", "")
        _record("read_file", {"path": f}, reward, done)
        file_contents[f] = content

    # ── Step 4+5: LLM fix → edit_file (one shot per file) ────────────────────
    for fname in files:
        if success:
            break

        current_content = file_contents.get(fname, "(file not yet read)")
        prompt = (
            f"You are a Python bug fixer. Fix the file '{fname}'.\n\n"
            f"Test failures:\n{test_logs}\n\n"
            f"Current content of '{fname}':\n{current_content}\n\n"
            f"Output ONLY the complete corrected Python code for '{fname}'.\n"
            "Rules:\n"
            "- Do NOT include any explanation or comments about the fix.\n"
            "- Do NOT use markdown fences (no ``` markers).\n"
            "- Write the FULL file content from the first line to the last.\n"
            "- If the fix is a missing colon, add it. If it is wrong logic, correct it.\n"
            "- Do NOT add a filename comment (e.g. # broken_code.py) at the top.\n"
        )

        try:
            response = client.chat.completions.create(
                model=os.environ["MODEL_NAME"],
                messages=[{"role": "user", "content": prompt}],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
            )
            raw = response.choices[0].message.content or ""
        except (RateLimitError, APIError) as e:
            logger.error(f"LLM error for '{fname}': {e}")
            continue

        logger.info(f"LLM raw response for '{fname}': {raw[:300]!r}")

        new_content = _extract_code(raw)
        if not new_content:
            logger.warning(f"LLM returned empty content for '{fname}' — skipping")
            continue

        res = await _call("edit_file", {"path": fname, "content": new_content})
        reward, done = res.get("reward", 0.0), res.get("done", False)
        _record("edit_file", {"path": fname}, reward, done)

    # ── Remove Generated Solution ──────────────────────────────────────────────
    for fname in files:
        original = file_contents.get(fname)
        if original:
            await env_step(env_url, "edit_file", {"path": fname, "content": original}, delay_ms=0)

    elapsed_ms   = int((datetime.now(timezone.utc) - start_ts).total_seconds() * 1000)
    final_reward = rewards[-1] if rewards else 0.0
    rewards_str  = ",".join(f"{r:.2f}" for r in rewards)

    print(
        f"[END] success={str(success).lower()} steps={global_step} "
        f"score={final_reward:.2f} rewards={rewards_str}",
        flush=True
    )

    return {
        "run_number":   run_number,
        "success":      success,
        "final_reward": final_reward,
        "rewards":      rewards,
        "steps":        steps_detail,
        "tools_used":   tools_used,
        "elapsed_ms":   elapsed_ms,
    }


# ── Statistics ───────────────────────────────────────────────────────────────────

def calculate_statistics(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    total     = len(runs)
    n_success = sum(1 for r in runs if r["success"])

    pass_at = {}
    for k in range(1, total + 1):
        if total - n_success < k:
            pass_at[f"pass@{k}"] = 1.0
        else:
            pass_at[f"pass@{k}"] = 1.0 - comb(total - n_success, k) / comb(total, k)

    tool_counts: Dict[str, int] = {}
    for r in runs:
        for t in r["tools_used"]:
            tool_counts[t] = tool_counts.get(t, 0) + 1

    return {
        "total_runs":        total,
        "successful_runs":   n_success,
        "success_rate":      n_success / total if total else 0.0,
        **pass_at,
        "avg_steps_per_run": round(sum(len(r["rewards"]) for r in runs) / total if total else 0, 2),
        "avg_final_reward":  round(sum(r["final_reward"] for r in runs) / total if total else 0, 4),
        "mean_elapsed_ms":   round(sum(r["elapsed_ms"]   for r in runs) / total if total else 0, 0),
        "tool_usage":        tool_counts,
    }


def _save_results(all_runs: List[Dict], config: Dict, out_file: str) -> None:
    """Write partial or final results to JSON — called after every run."""
    stats  = calculate_statistics(all_runs)
    output = {
        "benchmark_config": {
            "task":              config["task"],
            "model":             config["model_name"],
            "api_base_url":      config["api_base_url"],
            "number_of_runs":    config["number_of_runs"],
            "max_steps_per_run": config["max_steps_per_run"],
            "temperature":       config["temperature"],
        },
        "runs":       all_runs,
        "statistics": stats,
    }
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2, default=str)


# ── Main ─────────────────────────────────────────────────────────────────────────

async def main(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if config is None:
        config = get_config()

    try:
        _validate_config(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    tasks_input = config["task"].split(",") if "," in config["task"] else [config["task"]]
    tasks = [f"task{i}" for i in range(1, 10)] if "all" in tasks_input else tasks_input
    n_runs = config["number_of_runs"]
    client = _init_client()

    all_tasks_results = {}

    for task in tasks:
        config["task"] = task
        logger.info("=" * 70)
        logger.info("DEBUG-ENV BENCHMARK")
        logger.info(f"task={task}  model={config['model_name']}  runs={n_runs}  max_steps={config['max_steps_per_run']}")
        logger.info(f"endpoint={config['api_base_url']}")
        logger.info("=" * 70)

        all_runs: List[Dict[str, Any]] = []
        ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_file = f"results_{task}_{ts}.json"

        for run_number in range(1, n_runs + 1):
            try:
                result = await execute_run(run_number, client, config)
                all_runs.append(result)
            except Exception as e:
                logger.error(f"Run {run_number} failed: {e}", exc_info=True)
                all_runs.append({
                    "run_number":   run_number,
                    "success":      False,
                    "final_reward": 0.0,
                    "rewards":      [],
                    "steps":        [],
                    "tools_used":   [],
                    "elapsed_ms":   0,
                    "error":        str(e),
                })

            # Save after every run so partial results are never lost
            _save_results(all_runs, config, out_file)
            logger.info(f"Results saved → {out_file}  (run {run_number}/{n_runs})")

            if all_runs[-1]["success"]:
                logger.info(f"Task {task} solved successfully on run {run_number}. Moving to next task.")
                break

        stats = calculate_statistics(all_runs)

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
        
        all_tasks_results[task] = {"benchmark_config": config.copy(), "runs": all_runs, "statistics": stats}

    return all_tasks_results


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted — partial results already saved to disk.")
