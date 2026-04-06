"""
Task 9: Collaborative Architecture Refactoring Seed Data

Complex collaborative scenario: Multiple developers refactor architecture
in parallel while maintaining integration and consistency.
"""

from typing import Any, Dict


def get_task9_seed_data() -> Dict[str, Any]:
    """
    Generate seed data for task9 (Collaborative Architecture Refactoring).

    Scenario:
      Large refactoring to break circular dependencies and improve testability.
      Multiple developers work on different modules in parallel.

      Alice (Senior) designs architecture, reviews all changes
      Bob (Junior) refactors data processing layer
      Carol (QA) refactors business logic, ensures test compatibility
      Dave (Lead) coordinates integration, resolves conflicts

    Current problems:
      - Circular imports: module_a imports module_b, module_b imports module_a
      - Tight coupling: Direct instantiation instead of dependency injection
      - Missing abstractions: No interfaces/base classes
      - Scattered validation: Same logic duplicated across modules
      - Difficult to test: Can't instantiate modules independently

    Refactoring goals:
      1. Extract common Processor abstract base class
      2. Use dependency injection instead of direct instantiation
      3. Create Validator class to consolidate validation
      4. Remove circular dependencies via interface abstraction
      5. Make each module independently testable
      6. Improve error handling with custom exceptions
    """
    return {
        "files": {
            "data_processor.py": get_data_processor_content(),
            "business_logic.py": get_business_logic_content(),
            "api_interface.py": get_api_interface_content(),
            "integration.py": get_integration_content(),
        },
        "test_file": "test_refactoring.py",
        "participants": [
            {
                "user_id": "alice_senior",
                "role": "architect",
                "responsibility": "Design refactoring, review changes, ensure consistency",
                "status": "in_progress",
            },
            {
                "user_id": "bob_junior",
                "role": "contributor",
                "responsibility": "Refactor data_processor.py following architecture",
                "status": "in_progress",
            },
            {
                "user_id": "carol_qa",
                "role": "contributor",
                "responsibility": "Refactor business_logic.py, ensure test compatibility",
                "status": "pending",
            },
            {
                "user_id": "dave_lead",
                "role": "integration_lead",
                "responsibility": "Coordinate integration, resolve conflicts, final merge",
                "status": "pending",
            },
        ],
        "current_issues": [
            "Circular import: data_processor ↔ business_logic ↔ api_interface",
            "Tight coupling: Direct instantiation of dependencies",
            "Broken abstraction: Direct access to private attributes",
            "Duplicated validation logic across modules",
            "Tests require full integration (can't unit test modules)",
            "Error handling inconsistent across modules",
        ],
        "refactoring_steps": [
            "Step 1: Design shared Processor interface (Alice)",
            "Step 2: Create Validator class (Alice)",
            "Step 3: Create custom exceptions (Alice)",
            "Step 4: Refactor data_processor.py (Bob)",
            "Step 5: Refactor business_logic.py (Carol)",
            "Step 6: Update api_interface.py (Carol or Bob)",
            "Step 7: Update integration.py for dependency injection (Alice)",
            "Step 8: Verify all modules integrate correctly (Dave)",
            "Step 9: Run full test suite (All)",
        ],
        "shared_artifacts_to_create": [
            "base_processor.py (abstract Processor class)",
            "validators.py (consolidated Validator class)",
            "exceptions.py (custom exception classes)",
        ],
        "expected_challenges": [
            "Parallel changes to shared interfaces cause conflicts",
            "Some code still depends on old circular import structure",
            "Test suite needs updating for new module structure",
            "Circular import detection not obvious at first",
        ],
        "tools_to_use": [
            "list_directory",
            "get_file_structure",
            "get_dependencies",
            "search_code",
            "read_file",
            "edit_file",
            "run_tests",
            "run_type_check",
            "get_test_coverage",
        ],
        "difficulty": "hard",
    }


def get_data_processor_content() -> str:
    """Get data_processor.py with circular dependency and tight coupling."""
    return '''"""
Data Processing Module

BUG: Has circular import with business_logic.py
BUG: Directly instantiates BusinessLogic (tight coupling)
BUG: Validation logic duplicated elsewhere
"""

# BUG: Circular import (business_logic imports this too)
from business_logic import BusinessLogic


class DataProcessor:
    """Process data - currently tightly coupled and hard to test."""

    def __init__(self):
        """Initialize processor."""
        self._data = []
        # BUG: Direct instantiation creates circular dependency
        self._logic = BusinessLogic()

    def load(self, data):
        """Load data."""
        # BUG: Validation logic - also exists in BusinessLogic
        if not data or not isinstance(data, list):
            raise ValueError("Data must be non-empty list")
        self._data = data

    def process(self):
        """Process data through business logic."""
        # BUG: Direct access to private attribute
        self._logic._validate()
        return self._logic._execute(self._data)

    def validate(self):
        """Validate data - DUPLICATED from BusinessLogic."""
        if not self._data:
            return False
        return all(isinstance(x, (int, str)) for x in self._data)
'''


def get_business_logic_content() -> str:
    """Get business_logic.py with circular dependency."""
    return '''"""
Business Logic Module

BUG: Has circular import with data_processor.py
BUG: Directly instantiates DataProcessor (tight coupling)
BUG: Validation duplicated
"""

# BUG: Circular import (data_processor imports this too)
from data_processor import DataProcessor


class BusinessLogic:
    """Business logic - currently has circular dependency."""

    def __init__(self):
        """Initialize."""
        self._cache = {}
        # BUG: Direct instantiation
        self._processor = DataProcessor()

    def _validate(self):
        """Validate - DUPLICATED validation logic."""
        if not hasattr(self._processor, "_data"):
            return False
        return len(self._processor._data) > 0

    def _execute(self, data):
        """Execute business logic."""
        # BUG: Inconsistent error handling
        try:
            result = [f"processed_{item}" for item in data]
            return result
        except Exception as e:
            # BUG: Generic error handling
            return []

    def run(self, data):
        """Run with data."""
        self._processor.load(data)
        if not self._processor.validate():
            # BUG: Inconsistent error handling
            raise RuntimeError("Invalid data")
        return self._execute(data)
'''


def get_api_interface_content() -> str:
    """Get api_interface.py."""
    return '''"""
API Interface Module

BUG: Direct instantiation of BusinessLogic
"""

from business_logic import BusinessLogic


class APIInterface:
    """API interface - tight coupling to BusinessLogic."""

    def __init__(self):
        """Initialize."""
        # BUG: Direct instantiation
        self._logic = BusinessLogic()

    def process_request(self, data):
        """Process request."""
        # BUG: No input validation at API boundary
        result = self._logic.run(data)
        return {"status": "success", "data": result}

    def validate_request(self, data):
        """Validate request - should be here, not scattered."""
        # BUG: Validation scattered across modules
        if not data:
            return False
        return isinstance(data, list)
'''


def get_integration_content() -> str:
    """Get integration.py."""
    return '''"""
Integration Module

Currently mixes orchestration with business logic.
After refactoring, should use dependency injection.
"""

from api_interface import APIInterface


def main():
    """Main integration - currently creates tight coupling."""
    # BUG: Integration logic mixes with instantiation
    api = APIInterface()

    # BUG: No way to swap implementations for testing
    data = ["apple", "banana", "cherry"]

    try:
        response = api.process_request(data)
        print("Success:", response)
    except Exception as e:
        print("Error:", e)

    return response


if __name__ == "__main__":
    main()
'''


def get_test_file_content() -> str:
    """Get test_refactoring.py."""
    return '''"""
Integration tests for refactoring validation.

Current structure makes unit testing difficult.
After refactoring, should be easier to test modules independently.
"""

import pytest


# NOTE: Current tests are difficult because modules are tightly coupled
# After refactoring with dependency injection, tests should be cleaner


def test_data_processor_load():
    """Test DataProcessor load - currently requires full setup."""
    # BUG: Can't test DataProcessor alone due to circular import
    # After refactoring: Should work independently
    pass


def test_business_logic_execute():
    """Test BusinessLogic execute - currently requires DataProcessor."""
    # BUG: Can't test BusinessLogic independently
    # After refactoring: Should inject mocked DataProcessor
    pass


def test_api_interface_request():
    """Test APIInterface request - currently full stack."""
    # BUG: Tests full stack, not individual components
    # After refactoring: Should test API layer independently
    pass


def test_validation_consistency():
    """Test that validation logic is consistent across modules."""
    # BUG: Validation is duplicated - hard to test consistently
    # After refactoring: Should have single Validator
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''