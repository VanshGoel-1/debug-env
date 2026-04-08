"""
Curriculum dataset builder for GRPO training.

Converts TASK_REGISTRY into a HuggingFace Dataset ordered by difficulty
(easy → medium → hard). Each row is one prompt the model will be asked to complete.

Easy tasks are repeated more often so the model builds base competence first
(from Daniel's GPU Mode talk: "probability of good answer must be > 0").
"""

from datasets import Dataset

from debug_env.server.tasks.data import TASK_REGISTRY

DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}

PROMPT_TEMPLATE = """You are a Python debugging agent. Fix the broken code in the working directory.

Workflow:
1. list_files — discover what files exist
2. run_tests — see what is failing
3. read_file(path) — read each relevant file
4. edit_file(path, content) — write the complete corrected file
5. run_tests — confirm all tests pass (reward=1.0)

Rules:
- Read ALL files before editing — bugs can span multiple files
- edit_file replaces the ENTIRE file — always provide complete content
- Do NOT stop until reward=1.0

Task: {task_id}
Difficulty: {difficulty}
Description: {description}

Begin with list_files."""


def build_dataset(repeat_easy: int = 10, repeat_medium: int = 6, repeat_hard: int = 3) -> Dataset:
    """
    Build curriculum-ordered dataset from TASK_REGISTRY.

    Args:
        repeat_easy: How many times to repeat each easy task row.
        repeat_medium: How many times to repeat each medium task row.
        repeat_hard: How many times to repeat each hard task row.

    Returns:
        HuggingFace Dataset with columns: prompt, task_id, difficulty.
    """
    rows = []
    repeats = {"easy": repeat_easy, "medium": repeat_medium, "hard": repeat_hard}

    for task_id, meta in sorted(
        TASK_REGISTRY.items(),
        key=lambda x: DIFFICULTY_ORDER.get(x[1].get("difficulty", "medium"), 1),
    ):
        difficulty = meta.get("difficulty", "medium")
        n = repeats.get(difficulty, 4)
        for _ in range(n):
            rows.append(
                {
                    "prompt": PROMPT_TEMPLATE.format(
                        task_id=task_id,
                        difficulty=difficulty,
                        description=meta.get("description", ""),
                    ),
                    "task_id": task_id,
                    "difficulty": difficulty,
                }
            )

    return Dataset.from_list(rows)
