"""
Multi-User Sample Data for Debug Environment

Demonstrates collaborative debugging scenarios with multiple users,
roles, and access patterns.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List


def get_multi_user_sample_data() -> Dict[str, Any]:
    """
    Generate multi-user sample data for collaborative debugging scenarios.

    Users:
      - alice_senior: Senior developer (can assign, review, approve)
      - bob_junior: Junior developer (can fix, needs review)
      - carol_qa: QA engineer (reports bugs, verifies fixes)
      - dave_lead: Tech lead (oversight, final approval)

    Scenarios:
      1. Code Review Workflow: Junior submits fix, senior reviews
      2. Cross-team Bug Investigation: QA reports, dev investigates, lead coordinates
      3. Collaborative Refactoring: Multiple devs, different responsibilities
    """
    return {
        "users": get_users(),
        "roles": get_roles(),
        "permissions": get_permissions(),
        "tasks_metadata": get_tasks_metadata(),
        "description": "Multi-user collaboration scenarios for debugging benchmark",
    }


def get_users() -> List[Dict[str, Any]]:
    """Get sample users with different roles and permissions."""
    return [
        {
            "user_id": "alice_senior",
            "name": "Alice Chen",
            "role": "Senior Developer",
            "email": "alice.chen@company.com",
            "experience_level": "senior",
            "timezone": "America/New_York",
            "created_at": datetime.now().isoformat(),
        },
        {
            "user_id": "bob_junior",
            "name": "Bob Kumar",
            "role": "Junior Developer",
            "email": "bob.kumar@company.com",
            "experience_level": "junior",
            "timezone": "America/Los_Angeles",
            "created_at": datetime.now().isoformat(),
        },
        {
            "user_id": "carol_qa",
            "name": "Carol Martinez",
            "role": "QA Engineer",
            "email": "carol.martinez@company.com",
            "experience_level": "mid",
            "timezone": "America/Chicago",
            "created_at": datetime.now().isoformat(),
        },
        {
            "user_id": "dave_lead",
            "name": "Dave Thompson",
            "role": "Tech Lead",
            "email": "dave.thompson@company.com",
            "experience_level": "senior",
            "timezone": "America/New_York",
            "created_at": datetime.now().isoformat(),
        },
    ]


def get_roles() -> List[Dict[str, Any]]:
    """Get role definitions with permission levels."""
    return [
        {
            "role_id": "senior_dev",
            "name": "Senior Developer",
            "permissions": ["read", "write", "review", "approve", "assign"],
            "description": "Can fix bugs, review code, approve changes",
        },
        {
            "role_id": "junior_dev",
            "name": "Junior Developer",
            "permissions": ["read", "write", "request_review"],
            "description": "Can fix assigned bugs, needs review for approval",
        },
        {
            "role_id": "qa",
            "name": "QA Engineer",
            "permissions": ["read", "report", "verify"],
            "description": "Can report bugs, verify fixes",
        },
        {
            "role_id": "tech_lead",
            "name": "Tech Lead",
            "permissions": ["read", "write", "review", "approve", "assign", "oversight"],
            "description": "Overall oversight, assigns work, final approval",
        },
    ]


def get_permissions() -> List[Dict[str, Any]]:
    """Get permission definitions."""
    return [
        {
            "permission_id": "read",
            "name": "Read Code",
            "description": "Can view task code and details",
        },
        {
            "permission_id": "write",
            "name": "Write/Edit",
            "description": "Can edit task files and make changes",
        },
        {
            "permission_id": "review",
            "name": "Review Code",
            "description": "Can review and comment on changes",
        },
        {
            "permission_id": "approve",
            "name": "Approve",
            "description": "Can approve changes for completion",
        },
        {
            "permission_id": "assign",
            "name": "Assign Work",
            "description": "Can assign tasks to other users",
        },
        {
            "permission_id": "report",
            "name": "Report Issues",
            "description": "Can report new bugs/issues",
        },
        {
            "permission_id": "verify",
            "name": "Verify Fixes",
            "description": "Can verify that fixes work correctly",
        },
        {
            "permission_id": "oversight",
            "name": "Oversight",
            "description": "Overall visibility and coordination",
        },
    ]


def get_tasks_metadata() -> List[Dict[str, Any]]:
    """Get multi-user task scenarios."""
    base_date = datetime.now()

    return [
        {
            "task_id": "task7",
            "title": "Code Review Workflow",
            "description": "Junior developer submits a fix that needs code review and approval from senior developer",
            "difficulty": "medium",
            "scenario_type": "code_review",
            "participants": [
                {
                    "user_id": "bob_junior",
                    "role": "assignee",
                    "responsibility": "Fix the bug and submit for review",
                    "status": "in_progress",
                },
                {
                    "user_id": "alice_senior",
                    "role": "reviewer",
                    "responsibility": "Review code, provide feedback, approve if acceptable",
                    "status": "pending",
                },
                {
                    "user_id": "dave_lead",
                    "role": "observer",
                    "responsibility": "Oversee process, escalate if needed",
                    "status": "pending",
                },
            ],
            "workflow_steps": [
                "Step 1: Bob reads the failing code and tests",
                "Step 2: Bob fixes the bug in the code",
                "Step 3: Bob runs tests to verify the fix",
                "Step 4: Alice reviews Bob's code changes",
                "Step 5: Alice checks test coverage and design",
                "Step 6: Alice approves and merges the fix",
            ],
            "expected_issues": [
                "Code doesn't follow team style guidelines",
                "Missing test coverage for edge case",
                "Incomplete error handling",
            ],
            "tools_available": [
                "read_file",
                "edit_file",
                "run_tests",
                "search_code",
                "get_file_structure",
                "run_type_check",
                "get_test_coverage",
            ],
            "created_at": base_date.isoformat(),
            "due_date": (base_date + timedelta(days=2)).isoformat(),
        },
        {
            "task_id": "task8",
            "title": "Cross-team Bug Investigation",
            "description": "QA reported a complex bug. Dev team needs to investigate, communicate findings, and fix collaboratively",
            "difficulty": "hard",
            "scenario_type": "cross_team_collaboration",
            "participants": [
                {
                    "user_id": "carol_qa",
                    "role": "bug_reporter",
                    "responsibility": "Provide bug details, reproduction steps, verify fix",
                    "status": "completed",
                },
                {
                    "user_id": "bob_junior",
                    "role": "investigator",
                    "responsibility": "Investigate root cause, document findings",
                    "status": "in_progress",
                },
                {
                    "user_id": "alice_senior",
                    "role": "problem_solver",
                    "responsibility": "Propose solution, implement fix, ensure quality",
                    "status": "pending",
                },
                {
                    "user_id": "dave_lead",
                    "role": "coordinator",
                    "responsibility": "Coordinate team, resolve blockers, approve solution",
                    "status": "pending",
                },
            ],
            "workflow_steps": [
                "Step 1: Carol (QA) reports bug: 'User profile update fails with invalid email'",
                "Step 2: Bob investigates the code path for email validation",
                "Step 3: Bob identifies the issue is in validation logic and documents findings",
                "Step 4: Alice reviews findings and designs a fix",
                "Step 5: Alice implements the fix and adds test coverage",
                "Step 6: Bob and Alice code review together",
                "Step 7: Carol verifies the fix in the updated code",
                "Step 8: Dave approves and coordinates merge",
            ],
            "bug_description": "User profile update fails with 'invalid email' error even for valid email addresses like 'user+tag@domain.com'",
            "root_cause": "Email validation regex too strict, doesn't handle '+' character in local part",
            "expected_issues": [
                "Validation logic is in the wrong module",
                "Multiple places need the same fix",
                "Missing test cases for email formats",
            ],
            "tools_available": [
                "read_file",
                "edit_file",
                "run_tests",
                "search_code",
                "get_file_structure",
                "get_dependencies",
                "run_type_check",
                "get_test_coverage",
            ],
            "created_at": base_date.isoformat(),
            "due_date": (base_date + timedelta(days=3)).isoformat(),
        },
        {
            "task_id": "task9",
            "title": "Collaborative Architecture Refactoring",
            "description": "Large refactoring involving multiple modules. Multiple devs contribute different parts, need to stay coordinated",
            "difficulty": "hard",
            "scenario_type": "team_refactoring",
            "participants": [
                {
                    "user_id": "alice_senior",
                    "role": "architect",
                    "responsibility": "Design refactoring strategy, review all changes, ensure consistency",
                    "status": "in_progress",
                },
                {
                    "user_id": "bob_junior",
                    "role": "contributor_1",
                    "responsibility": "Refactor module_a following architecture guidelines",
                    "status": "in_progress",
                },
                {
                    "user_id": "carol_qa",
                    "role": "contributor_2",
                    "responsibility": "Refactor module_b, ensure test compatibility",
                    "status": "pending",
                },
                {
                    "user_id": "dave_lead",
                    "role": "integration_lead",
                    "responsibility": "Coordinate across modules, resolve conflicts, ensure integration",
                    "status": "pending",
                },
            ],
            "workflow_steps": [
                "Step 1: Alice designs refactoring architecture and creates shared interface",
                "Step 2: Bob starts refactoring module_a to use new interface",
                "Step 3: Carol starts refactoring module_b in parallel",
                "Step 4: Both check for integration issues with shared interface",
                "Step 5: Alice reviews both changes for consistency",
                "Step 6: Dave coordinates final integration and merge",
                "Step 7: Full test suite runs on integrated changes",
            ],
            "refactoring_goals": [
                "Break circular dependencies between modules",
                "Extract common interface",
                "Improve testability through dependency injection",
                "Consolidate validation logic",
            ],
            "modules_involved": ["module_a.py", "module_b.py", "module_c.py", "integration.py"],
            "expected_issues": [
                "Integration points between modules are unclear",
                "Parallel changes create merge conflicts",
                "Some code depends on old interface",
            ],
            "tools_available": [
                "list_directory",
                "read_file",
                "edit_file",
                "run_tests",
                "search_code",
                "get_file_structure",
                "get_dependencies",
                "run_type_check",
                "get_test_coverage",
            ],
            "created_at": base_date.isoformat(),
            "due_date": (base_date + timedelta(days=5)).isoformat(),
        },
    ]


def get_multi_user_sql() -> str:
    """Generate SQL for multi-user sample data."""
    data = get_multi_user_sample_data()
    sql_statements = []

    # Header
    sql_statements.append("-- Multi-User Debug Environment Sample Data")
    sql_statements.append(f"-- Generated on: {datetime.now().isoformat()}")
    sql_statements.append("-- Contains collaborative debugging scenarios with multiple users and roles")
    sql_statements.append("")

    # Users
    sql_statements.append("-- Users")
    sql_statements.append(
        "INSERT INTO users (user_id, name, role, email, experience_level, timezone, created_at) VALUES"
    )
    user_values = []
    for user in data["users"]:
        user_values.append(
            f"('{user['user_id']}', '{user['name']}', '{user['role']}', "
            f"'{user['email']}', '{user['experience_level']}', '{user['timezone']}', "
            f"'{user['created_at']}')"
        )
    sql_statements.append(",\n".join(user_values) + ";")
    sql_statements.append("")

    # Roles
    sql_statements.append("-- Roles")
    sql_statements.append(
        "INSERT INTO roles (role_id, name, description) VALUES"
    )
    role_values = []
    for role in data["roles"]:
        permissions_str = ",".join(role["permissions"])
        role_values.append(
            f"('{role['role_id']}', '{role['name']}', '{role['description']}')"
        )
    sql_statements.append(",\n".join(role_values) + ";")
    sql_statements.append("")

    # Permissions
    sql_statements.append("-- Permissions")
    sql_statements.append(
        "INSERT INTO permissions (permission_id, name, description) VALUES"
    )
    perm_values = []
    for perm in data["permissions"]:
        perm_values.append(
            f"('{perm['permission_id']}', '{perm['name']}', '{perm['description']}')"
        )
    sql_statements.append(",\n".join(perm_values) + ";")
    sql_statements.append("")

    # Tasks Metadata
    sql_statements.append("-- Task Scenarios")
    sql_statements.append(
        "INSERT INTO task_scenarios (task_id, title, description, difficulty, scenario_type, created_at, due_date) VALUES"
    )
    task_values = []
    for task in data["tasks_metadata"]:
        description = task["description"].replace("'", "''")
        task_values.append(
            f"('{task['task_id']}', '{task['title']}', '{description}', "
            f"'{task['difficulty']}', '{task['scenario_type']}', "
            f"'{task['created_at']}', '{task['due_date']}')"
        )
    sql_statements.append(",\n".join(task_values) + ";")
    sql_statements.append("")

    return "\n".join(sql_statements)