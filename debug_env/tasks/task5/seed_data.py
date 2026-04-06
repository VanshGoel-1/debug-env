"""
Task 5: Unused Imports and Dead Code Seed Data

Comprehensive seed data for code quality task.
Contains Python code with unused imports, unused variables, and dead code paths
that can be found using search, dependency analysis, and code structure inspection.
"""

from typing import Any, Dict, List


def get_task5_seed_data() -> Dict[str, Any]:
    """
    Generate seed data for task5 (Unused Imports & Dead Code).

    Files:
      - messy_code.py: Module with unused imports and dead code

    Issues Present:
      1. Unused imports (json, urllib, sys)
      2. Unused imports from typing (Tuple, Callable, Dict)
      3. Unused variable assignments
      4. Dead code paths (unreachable due to early returns)
      5. Commented-out code blocks
      6. Unused function parameters
      7. Unused class attributes
    """
    return {
        "files": {
            "messy_code.py": get_messy_code_content(),
        },
        "test_file": "test_messy_code.py",
        "issues_to_fix": [
            "Remove unused import: json (line 3)",
            "Remove unused import: urllib (line 4)",
            "Remove unused import from typing: Tuple, Callable, Dict (line 6)",
            "Remove unused variable: config_data (line 20)",
            "Remove unused variable: temp_result (line 28)",
            "Remove dead code: parse_legacy_format function (lines 35-42)",
            "Remove dead code: return statement in process_data (line 59-60)",
            "Remove unused parameter: debug_mode in analyze_data (line 68)",
            "Remove unused class attribute: _cache in DataProcessor (line 77)",
            "Remove commented-out code blocks (lines 82-85, 95-98)",
        ],
        "tools_to_use": [
            "search_code",
            "get_file_structure",
            "get_dependencies",
            "edit_file",
            "run_tests",
        ],
        "difficulty": "medium",
    }


def get_messy_code_content() -> str:
    """Get the broken messy_code.py file content."""
    return '''"""
Messy module with unused imports, variables, and dead code.
Needs cleanup and refactoring.
"""

import json  # UNUSED
import urllib  # UNUSED
from typing import List, Optional
from typing import Tuple, Callable, Dict  # UNUSED: Tuple, Callable, Dict


def load_data(filename: str) -> List[str]:
    """Load data from file."""
    try:
        with open(filename, "r") as f:
            return f.readlines()
    except FileNotFoundError:
        # Unused variable assignment
        config_data = {"default": "path", "timeout": 30}
        return []


def process_data(items: List[str]) -> List[str]:
    """Process items."""
    # Unused variable
    temp_result = []

    results = []
    for item in items:
        results.append(item.strip().upper())

    # Dead code: unreachable due to early return
    return results
    unused_value = 999  # Unreachable
    processed = [x.lower() for x in results]  # Unreachable


def parse_legacy_format(data: str) -> Optional[str]:
    """
    Dead code function - never called.
    Parse data in legacy format.
    """
    # This entire function is dead code
    parts = data.split("|")
    if len(parts) != 3:
        return None
    return parts[1]


def analyze_data(
    items: List[str],
    debug_mode: bool = False,  # UNUSED parameter
) -> dict:
    """Analyze items and return summary."""
    # debug_mode is never used
    count = len(items)
    non_empty = len([x for x in items if x.strip()])

    return {
        "total": count,
        "non_empty": non_empty,
        "empty": count - non_empty,
    }


class DataProcessor:
    """Process data with potential for cleanup."""

    def __init__(self):
        """Initialize processor."""
        self.data = []
        self._cache = {}  # UNUSED: never read or written

    def process(self, items: List[str]) -> List[str]:
        """Process items."""
        # Commented-out code blocks
        # self._cache["processed"] = items
        # processed_items = self._preprocess(items)
        # results = self._apply_transformations(processed_items)

        results = []
        for item in items:
            results.append(item.strip().upper())

        # More commented code
        # self._cache["results"] = results
        # logger.debug(f"Processed {len(results)} items")

        return results

    def validate(self, items: List[str]) -> bool:
        """Validate items."""
        return len(items) > 0


def main():
    """Main entry point."""
    data = load_data("data.txt")
    processed = process_data(data)
    analysis = analyze_data(processed, debug_mode=True)

    processor = DataProcessor()
    result = processor.process(data)

    return {
        "processed": processed,
        "analysis": analysis,
        "result": result,
    }


if __name__ == "__main__":
    main()
'''


def get_test_file_content() -> str:
    """Get the test_messy_code.py file content."""
    return '''"""
Tests for messy_code module.
"""

import pytest
from messy_code import (
    load_data,
    process_data,
    analyze_data,
    DataProcessor,
    main,
)


def test_process_data():
    """Test process_data function."""
    input_data = ["hello", "world", "test"]
    result = process_data(input_data)

    assert len(result) == 3
    assert result[0] == "HELLO"
    assert result[1] == "WORLD"
    assert result[2] == "TEST"


def test_process_data_with_whitespace():
    """Test process_data with whitespace."""
    input_data = ["  hello  ", "\\tworld\\t", "\\n test "]
    result = process_data(input_data)

    assert result[0] == "HELLO"
    assert result[1] == "WORLD"
    assert result[2] == "TEST"


def test_analyze_data():
    """Test analyze_data function."""
    items = ["hello", "", "world", "", ""]
    result = analyze_data(items)

    assert result["total"] == 5
    assert result["non_empty"] == 2
    assert result["empty"] == 3


def test_analyze_data_all_non_empty():
    """Test analyze_data with all non-empty items."""
    items = ["a", "b", "c"]
    result = analyze_data(items)

    assert result["total"] == 3
    assert result["non_empty"] == 3
    assert result["empty"] == 0


def test_data_processor():
    """Test DataProcessor class."""
    processor = DataProcessor()
    data = ["test", "data", "items"]

    result = processor.process(data)
    assert len(result) == 3
    assert result[0] == "TEST"


def test_data_processor_validate():
    """Test DataProcessor validation."""
    processor = DataProcessor()

    assert processor.validate(["item"]) is True
    assert processor.validate([]) is False


def test_main():
    """Test main function."""
    # Note: This test will fail if data.txt doesn't exist
    # It's included to show the expected behavior
    try:
        result = main()
        assert result is not None
        assert "processed" in result
        assert "analysis" in result
    except FileNotFoundError:
        # Expected if data.txt doesn't exist
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''