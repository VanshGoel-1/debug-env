"""
Task 7: Code Review Workflow Seed Data

Collaborative scenario: Junior developer submits fix that needs code review.
Demonstrates multi-user workflow with approval gates.
"""

from typing import Any, Dict


def get_task7_seed_data() -> Dict[str, Any]:
    """
    Generate seed data for task7 (Code Review Workflow).

    Scenario:
      Bob (Junior Dev) found and fixed a bug in authentication logic.
      Alice (Senior Dev) needs to review the fix.
      Dave (Tech Lead) oversees the process.

    Workflow:
      1. Bob reads failing test and understands the bug
      2. Bob edits the authentication code to fix the issue
      3. Bob runs tests to verify the fix works
      4. Alice reviews the code changes
      5. Alice checks test coverage and style
      6. Alice approves the fix

    Issues to address:
      1. Code style doesn't match team standards
      2. Missing edge case test coverage
      3. Missing docstring on modified function
      4. Incomplete error handling
    """
    return {
        "files": {
            "auth.py": get_auth_py_content(),
            "test_auth.py": get_test_auth_py_content(),
        },
        "test_file": "test_auth.py",
        "participants": [
            {
                "user_id": "bob_junior",
                "role": "assignee",
                "responsibility": "Fix the bug, ensure tests pass",
                "status": "in_progress",
            },
            {
                "user_id": "alice_senior",
                "role": "reviewer",
                "responsibility": "Review code, check quality, approve",
                "status": "pending",
            },
            {
                "user_id": "dave_lead",
                "role": "observer",
                "responsibility": "Oversee, escalate if needed",
                "status": "pending",
            },
        ],
        "initial_state": "Bug reported: authenticate() returns True for invalid tokens",
        "expected_issues": [
            "Code style inconsistency (spacing, naming)",
            "Missing docstring on authenticate_token()",
            "Missing test for None token",
            "Incomplete error message in exception",
            "Missing type hints on helper function",
        ],
        "review_checklist": [
            "✗ Code style matches team guidelines",
            "✗ Test coverage is adequate",
            "✗ Docstrings present and clear",
            "✗ Error handling is complete",
            "✗ No security vulnerabilities introduced",
        ],
        "tools_to_use": [
            "read_file",
            "edit_file",
            "run_tests",
            "search_code",
            "run_type_check",
            "get_test_coverage",
        ],
        "difficulty": "medium",
    }


def get_auth_py_content() -> str:
    """Get the auth.py file with the bug to fix."""
    return '''"""
Authentication module with token validation.
"""

import re
from typing import Optional


def validate_token_format(token: str) -> bool:
    """Validate token format (basic pattern check)."""
    if not token or not isinstance(token, str):
        return False
    # Simple pattern: alphanumeric, at least 20 chars
    return bool(re.match(r"^[a-zA-Z0-9]{20,}$", token))


def check_token_expiry(token: str) -> bool:
    """Check if token is expired."""
    # Simplified: tokens with "expired" in them are expired
    return "expired" not in token.lower()


# Bug: This function has incorrect logic
def authenticate_token(token: str) -> bool:
    """
    Authenticate a user token.

    Args:
        token: The authentication token to validate

    Returns:
        True if token is valid, False otherwise
    """
    # BUG: Returns True for None/empty tokens
    if not validate_token_format(token):
        return True  # WRONG: Should return False

    # BUG: Doesn't check expiry
    return True  # WRONG: Should check expiry too


def authenticate(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.

    Args:
        username: The username
        password: The password (should be hashed)

    Returns:
        True if authenticated, False otherwise
    """
    # For this exercise, accept specific credentials
    if username == "admin" and password == "secret123":
        return True
    return False


def authenticate_with_token(token: str) -> bool:
    """Authenticate using a token."""
    # Uses the buggy function
    return authenticate_token(token)


def get_user_info(token: Optional[str]) -> dict:
    """Get user info if token is valid."""
    if token and authenticate_with_token(token):
        return {"user_id": "123", "username": "admin"}
    return {}
'''


def get_test_auth_py_content() -> str:
    """Get the test_auth.py file."""
    return '''"""
Tests for authentication module.
"""

import pytest
from auth import (
    validate_token_format,
    check_token_expiry,
    authenticate_token,
    authenticate,
    authenticate_with_token,
    get_user_info,
)


def test_validate_token_format_valid():
    """Test validate_token_format with valid tokens."""
    assert validate_token_format("abcd1234567890abcdef")
    assert validate_token_format("ABCDEF1234567890WXYZ")
    assert validate_token_format("a" * 50)  # Very long token


def test_validate_token_format_invalid():
    """Test validate_token_format with invalid tokens."""
    assert not validate_token_format("short")
    assert not validate_token_format("")
    assert not validate_token_format("token-with-dashes")
    assert not validate_token_format("token_with_underscores")


def test_validate_token_format_none():
    """Test validate_token_format with None."""
    assert not validate_token_format(None)


def test_check_token_expiry():
    """Test check_token_expiry function."""
    assert check_token_expiry("valid_token_abc123")
    assert not check_token_expiry("expired_token_xyz")
    assert not check_token_expiry("EXPIRED")


def test_authenticate_token_valid():
    """Test authenticate_token with valid token."""
    assert authenticate_token("validtoken12345678901")


def test_authenticate_token_invalid_format():
    """Test authenticate_token rejects invalid format."""
    assert not authenticate_token("short")
    assert not authenticate_token("")


def test_authenticate_token_expired():
    """Test authenticate_token rejects expired tokens."""
    assert not authenticate_token("expiredtoken12345678901")


def test_authenticate_token_none():
    """Test authenticate_token with None token."""
    assert not authenticate_token(None)


def test_authenticate_valid_credentials():
    """Test authenticate with valid credentials."""
    assert authenticate("admin", "secret123")


def test_authenticate_invalid_credentials():
    """Test authenticate with invalid credentials."""
    assert not authenticate("admin", "wrongpassword")
    assert not authenticate("unknownuser", "secret123")


def test_authenticate_with_token():
    """Test authenticate_with_token."""
    assert authenticate_with_token("validtoken12345678901")
    assert not authenticate_with_token("invalidtoken")
    assert not authenticate_with_token("expiredtoken12345678901")


def test_get_user_info_valid_token():
    """Test get_user_info with valid token."""
    info = get_user_info("validtoken12345678901")
    assert info.get("user_id") == "123"
    assert info.get("username") == "admin"


def test_get_user_info_invalid_token():
    """Test get_user_info with invalid token."""
    assert get_user_info("invalid") == {}
    assert get_user_info(None) == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''