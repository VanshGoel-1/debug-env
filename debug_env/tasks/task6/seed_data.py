"""
Task 6: Complex Multi-file Refactoring Seed Data

Comprehensive seed data for architectural refactoring task.
Contains multiple Python modules with architectural issues including:
- Circular dependencies
- Tight coupling between modules
- Broken abstraction layers
- Missing integration points
- Data flow inconsistencies
"""

from typing import Any, Dict, List


def get_task6_seed_data() -> Dict[str, Any]:
    """
    Generate seed data for task6 (Complex Multi-file Refactoring).

    Files:
      - module_a.py: Data processing module
      - module_b.py: Business logic module (depends on A)
      - module_c.py: API interface module
      - integration.py: Integration layer (coordination)

    Architectural Issues:
      1. Circular dependency: A ↔ B ↔ C
      2. Tight coupling: Direct object instantiation instead of DI
      3. Broken abstraction: B accesses A's internal state directly
      4. Inconsistent error handling across modules
      5. Missing interface definitions
      6. Data validation scattered across modules
      7. Integration logic mixed with business logic
      8. Test coverage gaps due to tight coupling

    Goal:
      Refactor to:
      - Break circular dependencies via dependency injection
      - Extract common interfaces
      - Consolidate validation logic
      - Improve separation of concerns
      - Make integration layer explicit
    """
    return {
        "files": {
            "module_a.py": get_module_a_content(),
            "module_b.py": get_module_b_content(),
            "module_c.py": get_module_c_content(),
            "integration.py": get_integration_content(),
        },
        "test_file": "test_integration.py",
        "architectural_issues": [
            "Circular import: module_a imports from module_b, module_b imports from module_a",
            "Tight coupling: ProcessorB directly instantiates ProcessorA",
            "Broken abstraction: ProcessorB accesses _raw_data (internal) from ProcessorA",
            "Inconsistent validation: validate() in A, validate() in B, no validation in C",
            "Missing interface: No abstract base for processors",
            "Data flow unclear: Integration happens in multiple places",
            "Error handling: Different exception patterns in each module",
            "Integration logic: BusinessLogic.execute() does too much",
        ],
        "refactoring_goals": [
            "Extract common processor interface (Processor ABC)",
            "Use dependency injection instead of instantiation",
            "Move validation to a dedicated Validator class",
            "Consolidate error handling with custom exceptions",
            "Make integration explicit via Integration class",
            "Break circular dependency via interface abstraction",
            "Separate concerns: each module has single responsibility",
        ],
        "tools_to_use": [
            "list_directory",
            "get_file_structure",
            "get_dependencies",
            "search_code",
            "get_test_coverage",
            "edit_file",
            "run_tests",
        ],
        "difficulty": "hard",
    }


def get_module_a_content() -> str:
    """Get module_a.py content."""
    return '''"""
Module A: Data Processing

Responsible for low-level data processing.
Currently has tight coupling to Module B.
"""


class ProcessorA:
    """Process raw data."""

    def __init__(self):
        """Initialize processor A."""
        self._raw_data = []
        self._processed = False

    def load(self, data: list) -> None:
        """Load raw data."""
        self._raw_data = data
        self._processed = False

    def validate(self) -> bool:
        """Validate raw data."""
        if not self._raw_data:
            return False
        # Basic validation
        return all(isinstance(x, (int, str)) for x in self._raw_data)

    def process(self) -> list:
        """Process the data."""
        if not self.validate():
            raise ValueError("Invalid data in ProcessorA")

        result = [str(x).upper() for x in self._raw_data]
        self._processed = True
        return result


def create_processor_a() -> ProcessorA:
    """Factory function for ProcessorA."""
    return ProcessorA()
'''


def get_module_b_content() -> str:
    """Get module_b.py content."""
    return '''"""
Module B: Business Logic

Contains business logic that depends on Module A.
Has circular dependency with Module A.
Tightly coupled to ProcessorA implementation.
"""

from module_a import ProcessorA, create_processor_a


class BusinessLogic:
    """Business logic processor."""

    def __init__(self):
        """Initialize business logic."""
        # Tight coupling: directly instantiates ProcessorA
        self.processor_a = create_processor_a()
        self._cache = {}

    def validate(self) -> bool:
        """Validate business logic state."""
        # Inconsistent validation logic
        if not hasattr(self.processor_a, "_raw_data"):
            return False
        return len(self.processor_a._raw_data) > 0  # Broken abstraction!

    def execute(self, data: list) -> dict:
        """
        Execute business logic.
        This method does too much (violates SRP).
        """
        # Load data
        self.processor_a.load(data)

        # Validate using ProcessorA
        if not self.processor_a.validate():
            raise ValueError("Data validation failed")

        # Process
        processed = self.processor_a.process()

        # Additional business logic
        enriched = [f"processed_{item}" for item in processed]

        # Direct access to internal state (broken abstraction)
        result = {
            "original_count": len(self.processor_a._raw_data),
            "processed_count": len(enriched),
            "processed_data": enriched,
        }

        # Cache management (integration concern mixed in)
        self._cache["last_result"] = result

        return result

    def get_last_result(self) -> dict:
        """Get cached result."""
        return self._cache.get("last_result", {})


def create_business_logic() -> BusinessLogic:
    """Factory function for BusinessLogic."""
    return BusinessLogic()
'''


def get_module_c_content() -> str:
    """Get module_c.py content."""
    return '''"""
Module C: API Interface

Provides API interface to the system.
Currently doesn't validate input (relies on downstream modules).
Has tight coupling to BusinessLogic.
"""

from module_b import create_business_logic


class APIEndpoint:
    """API endpoint interface."""

    def __init__(self):
        """Initialize API endpoint."""
        # Tight coupling: directly instantiates BusinessLogic
        self.business_logic = create_business_logic()

    def process_request(self, data: list) -> dict:
        """
        Process incoming request.
        No validation at API boundary!
        """
        # Should validate here, but doesn't
        result = self.business_logic.execute(data)
        return {
            "status": "success",
            "data": result,
        }

    def get_status(self) -> dict:
        """Get current status."""
        # Inconsistent error handling
        try:
            last_result = self.business_logic.get_last_result()
            return {
                "status": "ok",
                "last_result_size": len(last_result.get("processed_data", [])),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


def create_api_endpoint() -> APIEndpoint:
    """Factory function for APIEndpoint."""
    return APIEndpoint()
'''


def get_integration_content() -> str:
    """Get integration.py content."""
    return '''"""
Integration Module

Currently mixes integration logic with business logic.
No explicit integration layer.
"""

from module_c import create_api_endpoint


def main():
    """
    Main integration point.
    This is the only place orchestration happens,
    but orchestration logic is scattered across modules.
    """
    # Create API endpoint (which creates BusinessLogic, which creates ProcessorA)
    api = create_api_endpoint()

    # Process some data
    raw_data = ["apple", "banana", "cherry", 123]

    try:
        response = api.process_request(raw_data)
        print("Success:", response)
    except ValueError as e:
        print("Validation error:", e)
    except Exception as e:
        print("Unexpected error:", e)

    # Get status
    status = api.get_status()
    print("Status:", status)

    return response


if __name__ == "__main__":
    main()
'''


def get_test_file_content() -> str:
    """Get test_integration.py file content."""
    return '''"""
Integration tests for multi-module system.

These tests are difficult to write due to tight coupling.
They need to instantiate many objects at once.
"""

import pytest
from module_a import ProcessorA
from module_b import BusinessLogic
from module_c import APIEndpoint


def test_processor_a_basic():
    """Test ProcessorA basic functionality."""
    processor = ProcessorA()
    processor.load(["hello", "world"])

    assert processor.validate()
    assert processor.process() == ["HELLO", "WORLD"]


def test_processor_a_invalid_data():
    """Test ProcessorA with invalid data."""
    processor = ProcessorA()
    processor.load([None, {}])  # Invalid types

    assert not processor.validate()


def test_processor_a_empty_data():
    """Test ProcessorA with empty data."""
    processor = ProcessorA()
    processor.load([])

    assert not processor.validate()


def test_business_logic():
    """Test BusinessLogic execution."""
    bl = BusinessLogic()
    result = bl.execute(["test", "data"])

    assert result["processed_count"] == 2
    assert "processed_test" in result["processed_data"]


def test_business_logic_caching():
    """Test BusinessLogic result caching."""
    bl = BusinessLogic()

    result1 = bl.execute(["first"])
    cached = bl.get_last_result()

    assert cached == result1
    assert len(cached["processed_data"]) == 1


def test_api_endpoint():
    """Test APIEndpoint."""
    api = APIEndpoint()
    response = api.process_request(["api", "test"])

    assert response["status"] == "success"
    assert "data" in response


def test_api_status():
    """Test APIEndpoint status."""
    api = APIEndpoint()
    api.process_request(["test"])

    status = api.get_status()
    assert status["status"] == "ok"
    assert status["last_result_size"] == 1


def test_full_integration():
    """Test full system integration."""
    api = APIEndpoint()

    # Process data through full stack
    response = api.process_request(["integration", "test", "data"])

    assert response["status"] == "success"
    assert len(response["data"]["processed_data"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''