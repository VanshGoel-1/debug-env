"""
Task 4: Type Error Detection Seed Data

Comprehensive seed data for type error detection task.
Contains Python code with type hint mismatches and type incompatibilities
that can be found using mypy static type checking.
"""

from typing import Any, Dict, List


def get_task4_seed_data() -> Dict[str, Any]:
    """
    Generate seed data for task4 (Type Error Detection).

    Files:
      - typed_code.py: Main module with type annotations and errors
      - helper.py: Helper module with incompatible return types

    Type Errors Present:
      1. Function parameter type mismatch (passing str instead of int)
      2. Return type doesn't match annotation (returning None instead of str)
      3. Attribute access on potentially None type
      4. Incompatible type in assignment
      5. Missing argument in function call
      6. Wrong argument type in method call
    """
    return {
        "files": {
            "typed_code.py": get_typed_code_content(),
            "helper.py": get_helper_content(),
        },
        "test_file": "test_typed_code.py",
        "expected_issues": [
            "Line 15: Argument 1 to 'process_number' has incompatible type 'str'; expected 'int'",
            "Line 28: Incompatible return value type (got 'None', expected 'str')",
            "Line 37: Item 'None' has no attribute 'upper'",
            "Line 42: Incompatible types in assignment (expression has type 'int', variable has type 'str')",
            "Line 50: Missing positional argument 'required_param' in call to 'validate_input'",
            "Line 61: Argument 1 to 'calculate_average' has incompatible type 'list[str]'; expected 'list[int]'",
        ],
        "tools_to_use": [
            "run_type_check",
            "get_file_structure",
            "edit_file",
            "run_tests",
        ],
        "difficulty": "medium",
    }


def get_typed_code_content() -> str:
    """Get the broken typed_code.py file content."""
    return '''"""
Typed module with intentional type errors for debugging.
"""

from typing import Optional, List
from helper import safe_divide, validate_input


def process_number(value: int) -> int:
    """Process a number and return the result."""
    return value * 2


def calculate_stats(numbers: List[int]) -> str:
    """Calculate statistics and return formatted string."""
    if not numbers:
        return  # Type error: no return value when return type is str

    total = sum(numbers)
    average = total / len(numbers)
    return f"Average: {average}"


def format_name(name: Optional[str]) -> str:
    """Format and return a person's name."""
    if name:
        # Type error: name could be None, can't call .upper() on Optional[str]
        return name.upper()
    return "UNKNOWN"


def main():
    """Main function with multiple type errors."""
    # Type error: passing string instead of int
    result1 = process_number("42")

    # Type error: assigning int to str variable
    formatted_string: str = 100

    # Type error: missing required parameter
    validated = validate_input()

    # Type error: passing list of strings instead of list of ints
    stats = calculate_stats(["1", "2", "3"])

    # Correct usage for reference
    correct_result = process_number(42)
    correct_stats = calculate_stats([1, 2, 3])

    return {
        "result1": result1,
        "formatted_string": formatted_string,
        "validated": validated,
        "stats": stats,
        "correct_result": correct_result,
    }


if __name__ == "__main__":
    main()
'''


def get_helper_content() -> str:
    """Get the helper.py file content."""
    return '''"""
Helper module with type-hinted functions.
"""

from typing import List, Optional


def safe_divide(a: float, b: float) -> Optional[float]:
    """
    Safely divide two numbers, returning None if division by zero.

    Args:
        a: Numerator
        b: Denominator

    Returns:
        The result of a/b, or None if b is 0
    """
    if b == 0:
        return None
    return a / b


def validate_input(required_param: str, optional_param: Optional[str] = None) -> bool:
    """
    Validate input parameters.

    Args:
        required_param: A required string parameter
        optional_param: An optional string parameter

    Returns:
        True if input is valid, False otherwise
    """
    if not required_param:
        return False
    if optional_param is not None and len(optional_param) == 0:
        return False
    return True


def calculate_average(numbers: List[int]) -> float:
    """
    Calculate the average of a list of integers.

    Args:
        numbers: List of integers

    Returns:
        The average as a float

    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
'''


def get_test_file_content() -> str:
    """Get the test_typed_code.py file content."""
    return '''"""
Tests for typed_code module.
"""

import pytest
from typed_code import process_number, calculate_stats, format_name, main


def test_process_number():
    """Test process_number with valid input."""
    assert process_number(5) == 10
    assert process_number(0) == 0
    assert process_number(-3) == -6


def test_calculate_stats():
    """Test calculate_stats with various inputs."""
    assert "Average: 2.0" in calculate_stats([1, 2, 3])
    assert "Average: 5.5" in calculate_stats([5, 6])

    # Edge case: empty list
    assert calculate_stats([]) == ""


def test_format_name():
    """Test format_name with various inputs."""
    assert format_name("alice") == "ALICE"
    assert format_name("bob") == "BOB"
    assert format_name(None) == "UNKNOWN"


def test_main():
    """Test main function."""
    result = main()
    assert result is not None
    assert "result1" in result
    assert "formatted_string" in result
    assert "validated" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''