"""
Debug-Env Task Registry
Static task definitions for the debugging benchmark.
"""

from typing import Any, Dict, List

# Task metadata registry — mirrors the structure on disk under debug_env/tasks/
TASK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "task1": {
        "id": "task1",
        "title": "Syntax Error",
        "description": "Fix a Python syntax error that prevents the module from importing.",
        "difficulty": "easy",
        "bug_type": "syntax",
        "files": ["broken_code.py"],
    },
    "task2": {
        "id": "task2",
        "title": "Logic Error",
        "description": "Fix a logical error in a boolean expression.",
        "difficulty": "medium",
        "bug_type": "logic",
        "files": ["broken_code.py"],
    },
    "task3": {
        "id": "task3",
        "title": "Multi-file Bug",
        "description": "Fix a bug that spans broken_code.py and a helper module it imports.",
        "difficulty": "hard",
        "bug_type": "multi-file",
        "files": ["broken_code.py", "helper.py"],
    },
    "task4": {
        "id": "task4",
        "title": "Type Error Detection",
        "description": "Identify and fix type annotation errors detected by static type checking.",
        "difficulty": "medium",
        "bug_type": "type_error",
        "files": ["typed_code.py"],
        "tools": ["run_type_check", "edit_file", "run_tests"],
    },
    "task5": {
        "id": "task5",
        "title": "Unused Imports and Dead Code",
        "description": "Find and remove unused imports and dead code using code analysis tools.",
        "difficulty": "medium",
        "bug_type": "code_quality",
        "files": ["messy_code.py"],
        "tools": ["search_code", "get_file_structure", "get_dependencies", "edit_file", "run_tests"],
    },
    "task6": {
        "id": "task6",
        "title": "Complex Multi-file Refactoring",
        "description": "Refactor code across multiple files while maintaining test coverage and fixing architectural issues.",
        "difficulty": "hard",
        "bug_type": "architecture",
        "files": ["module_a.py", "module_b.py", "module_c.py", "integration.py"],
        "tools": ["list_directory", "get_file_structure", "get_dependencies", "search_code", "get_test_coverage", "edit_file", "run_tests"],
    },
    "task7": {
        "id": "task7",
        "title": "Code Review Workflow",
        "description": "Multi-user collaborative task: Junior developer submits fix that needs code review and approval",
        "difficulty": "medium",
        "bug_type": "code_quality",
        "files": ["auth.py", "test_auth.py"],
        "scenario_type": "code_review",
        "participants": ["bob_junior", "alice_senior", "dave_lead"],
        "tools": ["read_file", "edit_file", "run_tests", "search_code", "run_type_check", "get_test_coverage"],
    },
    "task8": {
        "id": "task8",
        "title": "Cross-team Bug Investigation",
        "description": "Multi-user collaborative task: QA reported bug, dev team investigates and implements fix",
        "difficulty": "hard",
        "bug_type": "bug_investigation",
        "files": ["user_service.py", "email_validator.py", "test_user_service.py"],
        "scenario_type": "cross_team_collaboration",
        "participants": ["carol_qa", "bob_junior", "alice_senior", "dave_lead"],
        "tools": ["search_code", "get_file_structure", "read_file", "run_tests", "edit_file", "get_test_coverage"],
    },
    "task9": {
        "id": "task9",
        "title": "Collaborative Architecture Refactoring",
        "description": "Multi-user collaborative task: Large refactoring with multiple developers working in parallel",
        "difficulty": "hard",
        "bug_type": "architecture",
        "files": ["data_processor.py", "business_logic.py", "api_interface.py", "integration.py"],
        "scenario_type": "team_refactoring",
        "participants": ["alice_senior", "bob_junior", "carol_qa", "dave_lead"],
        "tools": ["list_directory", "get_file_structure", "get_dependencies", "search_code", "read_file", "edit_file", "run_tests", "run_type_check", "get_test_coverage"],
    },
}


def get_task_by_id(task_id: str) -> Dict[str, Any]:
    """
    Return metadata for a task by its ID.

    Args:
        task_id: e.g. "task1"

    Returns:
        Task metadata dict.

    Raises:
        ValueError: If task_id is not registered.
    """
    task = TASK_REGISTRY.get(task_id)
    if task is None:
        available = get_available_task_ids()
        raise ValueError(f"Unknown task '{task_id}'. Available: {available}")
    return task


def get_available_task_ids() -> List[str]:
    """Return a sorted list of all registered task IDs."""
    return sorted(TASK_REGISTRY.keys())


def get_task_files(task_id: str) -> List[str]:
    """
    Return the list of source files belonging to a task.

    Args:
        task_id: e.g. "task1"

    Returns:
        List of filenames, e.g. ["broken_code.py", "helper.py"]
    """
    return get_task_by_id(task_id)["files"]


def validate_task_id(task_id: str) -> bool:
    """
    Check whether a task ID is registered.

    Args:
        task_id: The task ID to validate.

    Returns:
        True if the task exists, False otherwise.
    """
    return task_id in TASK_REGISTRY
