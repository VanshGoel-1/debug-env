"""
Task 8: Cross-team Bug Investigation Seed Data

Collaborative scenario: QA reported a bug, dev team must investigate and fix.
Demonstrates multi-user workflow with investigation and coordination.
"""

from typing import Any, Dict


def get_task8_seed_data() -> Dict[str, Any]:
    """
    Generate seed data for task8 (Cross-team Bug Investigation).

    Scenario:
      Carol (QA) reported: "User profile update fails with 'invalid email' error"
      Bug details: Valid emails like "user+tag@domain.com" are rejected

      Bob (Junior Dev) investigates and documents findings
      Alice (Senior Dev) designs and implements the fix
      Dave (Tech Lead) coordinates and approves

    Root cause: Email validation regex is too strict

    Workflow:
      1. Understand the bug from Carol's report
      2. Investigate the code to find where validation happens
      3. Identify the regex pattern that's too restrictive
      4. Search for all places email is validated
      5. Design a fix that handles edge cases
      6. Fix validation and add comprehensive tests
      7. Verify fix works for reported and edge cases
      8. Get approval from senior dev and tech lead
    """
    return {
        "files": {
            "user_service.py": get_user_service_content(),
            "email_validator.py": get_email_validator_content(),
            "test_user_service.py": get_test_user_service_content(),
        },
        "test_file": "test_user_service.py",
        "bug_report": {
            "reporter": "carol_qa",
            "title": "User profile update fails with invalid email",
            "description": "Users cannot update their profile with valid email addresses containing '+' character",
            "reproduction_steps": [
                "1. Go to user profile settings",
                "2. Change email to 'user+tag@example.com'",
                "3. Click save/update",
                "4. Error: 'Invalid email format'",
            ],
            "expected_behavior": "Email should be accepted as it's valid per RFC 5322",
            "actual_behavior": "Email is rejected with validation error",
            "severity": "high",
            "affected_users": "Any user with '+' in their email (common for filtering/organizing)",
        },
        "participants": [
            {
                "user_id": "carol_qa",
                "role": "bug_reporter",
                "responsibility": "Provide details, verify fix",
                "status": "completed",
            },
            {
                "user_id": "bob_junior",
                "role": "investigator",
                "responsibility": "Investigate root cause",
                "status": "in_progress",
            },
            {
                "user_id": "alice_senior",
                "role": "problem_solver",
                "responsibility": "Design and implement fix",
                "status": "pending",
            },
            {
                "user_id": "dave_lead",
                "role": "coordinator",
                "responsibility": "Coordinate, approve solution",
                "status": "pending",
            },
        ],
        "investigation_questions": [
            "Where is email validation happening?",
            "What regex pattern is being used?",
            "Are there multiple places email is validated?",
            "What email formats should be supported?",
            "What test cases are missing?",
        ],
        "expected_issues": [
            "Regex pattern uses [a-zA-Z0-9] instead of allowing special chars",
            "Validation logic is duplicated in user_service.py",
            "Missing test cases for emails with '+' character",
            "Missing test cases for other valid formats (dots, hyphens)",
            "Error messages could be more helpful",
        ],
        "tools_to_use": [
            "search_code",
            "get_file_structure",
            "read_file",
            "run_tests",
            "edit_file",
            "get_test_coverage",
        ],
        "difficulty": "hard",
    }


def get_user_service_content() -> str:
    """Get user_service.py with the email validation bug."""
    return '''"""
User service module for user profile management.
Contains email validation logic.
"""

import re
from typing import Optional, Dict, Any
from email_validator import validate_email as external_validate_email


def validate_email_local(email: str) -> bool:
    """
    Validate email format using regex (BUGGY - too strict).

    BUG: This regex doesn't allow '+', '.', or '-' in the local part
    Common in real-world emails but not supported here.
    """
    if not email:
        return False
    # BUG: This pattern is too restrictive
    pattern = r"^[a-zA-Z0-9]+@[a-zA-Z0-9]+\\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def update_user_profile(user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user profile with new data.

    Args:
        user_id: User ID
        profile_data: Dict with fields to update (email, name, etc)

    Returns:
        Updated profile data

    Raises:
        ValueError: If validation fails
    """
    updated_profile = {"user_id": user_id}

    # Email validation using the buggy function
    if "email" in profile_data:
        email = profile_data["email"]
        # BUG: Uses the restrictive local validation
        if not validate_email_local(email):
            raise ValueError(f"Invalid email format: {email}")
        updated_profile["email"] = email

    if "name" in profile_data:
        updated_profile["name"] = profile_data["name"]

    if "phone" in profile_data:
        updated_profile["phone"] = profile_data["phone"]

    return updated_profile


def validate_user_data(user_data: Dict[str, Any]) -> bool:
    """
    Validate all user data before saving.

    BUG: Also uses the restrictive email validation
    """
    if "email" in user_data:
        # Duplicated validation logic
        if not validate_email_local(user_data["email"]):
            return False

    if "name" in user_data:
        if not user_data.get("name") or len(user_data["name"]) < 2:
            return False

    return True


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile data."""
    # Mock data
    return {
        "user_id": user_id,
        "name": "Test User",
        "email": "testuser@example.com",
        "phone": "555-1234",
    }
'''


def get_email_validator_content() -> str:
    """Get email_validator.py helper module."""
    return '''"""
Email validation utilities.
"""

import re


def validate_email(email: str, strict: bool = False) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate
        strict: If True, use strict validation rules

    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # Basic structure check
    if "@" not in email or "." not in email:
        return False

    local, domain = email.rsplit("@", 1)

    if not local or not domain:
        return False

    if strict:
        # Strict: only alphanumeric + underscore
        local_pattern = r"^[a-zA-Z0-9_]+$"
    else:
        # More permissive: allow common special chars
        local_pattern = r"^[a-zA-Z0-9.+\\-_]+$"

    domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9\\-]*[a-zA-Z0-9]\\.[a-zA-Z]{2,}$"

    return bool(re.match(local_pattern, local)) and bool(re.match(domain_pattern, domain))
'''


def get_test_user_service_content() -> str:
    """Get test_user_service.py file."""
    return '''"""
Tests for user service module.
"""

import pytest
from user_service import (
    validate_email_local,
    update_user_profile,
    validate_user_data,
    get_user_profile,
)


def test_validate_email_local_valid():
    """Test email validation with standard emails."""
    assert validate_email_local("user@example.com")
    assert validate_email_local("john@company.org")


def test_validate_email_local_plus_sign():
    """Test email validation with plus sign (CURRENTLY FAILS)."""
    # This is valid per RFC 5322 but our regex rejects it
    assert validate_email_local("user+tag@example.com")


def test_validate_email_local_dot_in_local():
    """Test email validation with dots (CURRENTLY FAILS)."""
    assert validate_email_local("first.last@example.com")


def test_validate_email_local_hyphen():
    """Test email validation with hyphen (CURRENTLY FAILS)."""
    assert validate_email_local("user-name@example.com")


def test_validate_email_local_invalid():
    """Test email validation with invalid formats."""
    assert not validate_email_local("invalid")
    assert not validate_email_local("@example.com")
    assert not validate_email_local("user@")
    assert not validate_email_local("")
    assert not validate_email_local(None)


def test_update_user_profile_basic():
    """Test updating user profile with valid email."""
    result = update_user_profile("user1", {"email": "user@example.com"})
    assert result["email"] == "user@example.com"


def test_update_user_profile_plus_email():
    """Test updating with plus-sign email (CURRENTLY FAILS)."""
    result = update_user_profile("user1", {"email": "user+tag@example.com"})
    assert result["email"] == "user+tag@example.com"


def test_update_user_profile_with_name():
    """Test updating profile with name."""
    result = update_user_profile("user1", {
        "email": "user@example.com",
        "name": "John Doe"
    })
    assert result["name"] == "John Doe"


def test_update_user_profile_invalid_email():
    """Test updating with invalid email raises error."""
    with pytest.raises(ValueError, match="Invalid email"):
        update_user_profile("user1", {"email": "invalid"})


def test_validate_user_data_valid():
    """Test user data validation."""
    assert validate_user_data({"email": "user@example.com", "name": "John"})


def test_validate_user_data_plus_email():
    """Test user data validation with plus-sign email (CURRENTLY FAILS)."""
    assert validate_user_data({"email": "user+tag@example.com"})


def test_validate_user_data_short_name():
    """Test user data validation with short name."""
    assert not validate_user_data({"name": "J"})


def test_get_user_profile():
    """Test getting user profile."""
    profile = get_user_profile("test_user")
    assert profile["user_id"] == "test_user"
    assert "email" in profile


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''