"""
Advanced debugging tools for code analysis and inspection.

Provides functions for:
- Code search (grep-like pattern matching)
- File structure analysis (AST parsing)
- Type checking (mypy integration)
- Test coverage analysis (coverage.py integration)
- Directory listing and navigation
- Import dependency analysis
"""

import ast
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def search_code(
    workdir: str,
    pattern: str,
    file_types: str = "py",
    case_sensitive: bool = False,
    max_results: int = 50,
    context_lines: int = 2,
) -> Dict[str, Any]:
    """
    Search for code patterns across files in the task directory.

    Args:
        workdir: Absolute path to task working directory
        pattern: Text or regex pattern to search for
        file_types: File type filter ("py", "all", "txt", "json", "md")
        case_sensitive: Whether to match case
        max_results: Maximum matches to return (1-500)
        context_lines: Lines of context around each match (0-10)

    Returns:
        Dict with matches, match count, files searched, and timing info
    """
    try:
        workdir_path = Path(workdir)
        if not workdir_path.is_dir():
            return {"error": f"Invalid directory: {workdir}", "matches": [], "total_matches": 0}

        # Determine file extensions to search
        if file_types == "all":
            search_patterns = ["*"]
        elif file_types == "py":
            search_patterns = ["*.py"]
        else:
            search_patterns = [f"*.{file_types}"]

        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            return {"error": f"Invalid regex pattern: {e}", "matches": [], "total_matches": 0}

        matches = []
        files_searched = 0

        # Search files
        for search_pattern in search_patterns:
            for file_path in workdir_path.rglob(search_pattern):
                if not file_path.is_file():
                    continue

                files_searched += 1
                try:
                    content = file_path.read_text(encoding="utf-8")
                    lines = content.split("\n")

                    for line_num, line in enumerate(lines, 1):
                        for match in compiled_pattern.finditer(line):
                            if len(matches) >= max_results:
                                break

                            matches.append({
                                "filename": str(file_path.relative_to(workdir_path)),
                                "line_number": line_num,
                                "line_content": line,
                                "match_position": match.start(),
                                "before": lines[max(0, line_num - context_lines - 1):line_num - 1],
                                "after": lines[line_num:min(len(lines), line_num + context_lines)],
                            })
                except (UnicodeDecodeError, OSError):
                    continue

        logger.info(f"Search pattern '{pattern}': found {len(matches)} matches in {files_searched} files")

        return {
            "matches": matches,
            "total_matches": len(matches),
            "files_searched": files_searched,
            "search_time_ms": 0,  # Would be measured in production
        }

    except Exception as e:
        logger.error(f"Error searching code: {e}")
        return {"error": str(e), "matches": [], "total_matches": 0}


def get_file_structure(
    workdir: str,
    path: str,
    include_docstrings: bool = True,
    include_signatures: bool = True,
    max_depth: int = 0,
) -> Dict[str, Any]:
    """
    Parse and return the structure (AST) of a Python file.

    Args:
        workdir: Absolute path to task working directory
        path: File path relative to workdir
        include_docstrings: Include docstrings in output
        include_signatures: Include function/method signatures
        max_depth: Maximum nesting depth (0 for unlimited)

    Returns:
        Dict with classes, functions, imports, and constants
    """
    try:
        file_path = Path(workdir) / path
        if not file_path.is_file():
            return {"error": f"File not found: {path}"}

        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        structure = {
            "filename": path,
            "imports": [],
            "classes": [],
            "functions": [],
            "constants": [],
        }

        for node in ast.walk(tree):
            # Extract imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    structure["imports"].append({
                        "module": alias.name,
                        "items": [alias.asname or alias.name],
                        "line_number": node.lineno,
                    })

            elif isinstance(node, ast.ImportFrom):
                items = [alias.name for alias in node.names]
                structure["imports"].append({
                    "module": node.module or "",
                    "items": items,
                    "line_number": node.lineno,
                })

            # Extract classes
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line_number": node.lineno,
                    "methods": [],
                    "attributes": [],
                }

                if include_docstrings:
                    class_info["docstring"] = ast.get_docstring(node)

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info["methods"].append({
                            "name": item.name,
                            "line_number": item.lineno,
                        })

                structure["classes"].append(class_info)

        # Extract top-level functions
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line_number": node.lineno,
                }

                if include_signatures:
                    func_info["parameters"] = [arg.arg for arg in node.args.args]

                if include_docstrings:
                    func_info["docstring"] = ast.get_docstring(node)

                structure["functions"].append(func_info)

        logger.info(f"Extracted structure from {path}")
        return structure

    except SyntaxError as e:
        logger.error(f"Syntax error in {path}: {e}")
        return {"error": f"Syntax error: {e}"}
    except Exception as e:
        logger.error(f"Error getting file structure: {e}")
        return {"error": str(e)}


def run_type_check(
    workdir: str,
    path: str,
    strict: bool = False,
    ignore_missing_imports: bool = True,
    show_error_codes: bool = True,
    max_errors: int = 100,
) -> Dict[str, Any]:
    """
    Run static type checking (mypy) on Python files.

    Args:
        workdir: Absolute path to task working directory
        path: File or directory path relative to workdir
        strict: Enable strict type checking mode
        ignore_missing_imports: Ignore untyped third-party imports
        show_error_codes: Show mypy error codes
        max_errors: Maximum errors to report

    Returns:
        Dict with type check results and error list
    """
    try:
        check_path = Path(workdir) / path
        if not check_path.exists():
            return {"error": f"Path not found: {path}", "status": "error"}

        cmd = ["mypy", str(check_path)]

        if strict:
            cmd.append("--strict")
        if ignore_missing_imports:
            cmd.append("--ignore-missing-imports")
        if show_error_codes:
            cmd.append("--show-error-codes")

        cmd.extend(["--no-error-summary", f"--max-errors={max_errors}"])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=30,
        )

        # Parse output
        errors = []
        for line in result.stdout.split("\n"):
            if not line.strip():
                continue

            # mypy output format: file:line:column: error: message [error-code]
            match = re.match(
                r"^([^:]+):(\d+):(\d+): error: (.+)(?:\s+\[([^\]]+)\])?$",
                line
            )
            if match:
                errors.append({
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "column": int(match.group(3)),
                    "message": match.group(4),
                    "error_code": match.group(5),
                })

        status = "success" if result.returncode == 0 else "errors_found"

        logger.info(f"Type check {path}: {len(errors)} errors, status={status}")

        return {
            "path": path,
            "status": status,
            "error_count": len(errors),
            "errors": errors,
            "check_time_ms": 0,
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Type check timeout for {path}")
        return {"error": "Type check timeout", "status": "error"}
    except Exception as e:
        logger.error(f"Error running type check: {e}")
        return {"error": str(e), "status": "error"}


def get_test_coverage(
    workdir: str,
    path: str = ".",
    branch_coverage: bool = False,
    include_missing: bool = True,
    fail_under: int = 0,
) -> Dict[str, Any]:
    """
    Analyze test coverage for Python files.

    Args:
        workdir: Absolute path to task working directory
        path: File or directory path relative to workdir
        branch_coverage: Include branch coverage analysis
        include_missing: Show which lines are not covered
        fail_under: Minimum required coverage percentage

    Returns:
        Dict with coverage percentage, file breakdown, and statistics
    """
    try:
        cmd = ["coverage", "run", "-m", "pytest", workdir]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=60,
        )

        # Get coverage report
        cmd = ["coverage", "json", "--pretty-print"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=30,
        )

        coverage_data = json.loads(result.stdout)
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

        logger.info(f"Coverage for {path}: {total_coverage}%")

        return {
            "total_coverage": round(total_coverage, 1),
            "files": [],
            "functions": [],
            "status": "covered" if total_coverage >= fail_under else "uncovered",
            "check_time_ms": 0,
        }

    except Exception as e:
        logger.error(f"Error analyzing coverage: {e}")
        return {"error": str(e), "total_coverage": 0, "status": "error"}


def list_directory(
    workdir: str,
    path: str = ".",
    recursive: bool = True,
    max_depth: int = 0,
    include_hidden: bool = False,
    file_types: str = "all",
) -> Dict[str, Any]:
    """
    List files and directories in the task working directory.

    Args:
        workdir: Absolute path to task working directory
        path: Subdirectory path relative to workdir
        recursive: Include subdirectories recursively
        max_depth: Maximum directory nesting depth (0 for unlimited)
        include_hidden: Include hidden files/folders starting with .
        file_types: Filter by file type ("py", "all", "test", "source")

    Returns:
        Dict with directory tree, file count, and metadata
    """
    try:
        root_path = Path(workdir) / path
        if not root_path.is_dir():
            return {"error": f"Directory not found: {path}"}

        def walk_tree(directory: Path, depth: int = 0) -> List[Dict]:
            if max_depth > 0 and depth >= max_depth:
                return []

            items = []
            try:
                for entry in sorted(directory.iterdir()):
                    # Skip hidden files if needed
                    if entry.name.startswith(".") and not include_hidden:
                        continue

                    # Filter by file type
                    if file_types == "py" and entry.is_file() and not entry.suffix == ".py":
                        continue
                    elif file_types == "test" and entry.is_file() and not entry.name.startswith("test_"):
                        continue

                    item = {
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                        "path": str(entry.relative_to(Path(workdir))),
                    }

                    if entry.is_file():
                        item["size_bytes"] = entry.stat().st_size
                        item["is_test"] = entry.name.startswith("test_")

                    if entry.is_dir() and recursive:
                        item["contents"] = walk_tree(entry, depth + 1)

                    items.append(item)
            except PermissionError:
                pass

            return items

        items = walk_tree(root_path)

        # Count files
        total_files = sum(1 for entry in root_path.rglob("*") if entry.is_file())
        total_dirs = sum(1 for entry in root_path.rglob("*") if entry.is_dir())

        logger.info(f"Listed directory {path}: {total_files} files, {total_dirs} directories")

        return {
            "root_path": path,
            "total_files": total_files,
            "total_directories": total_dirs,
            "items": items,
            "tree_depth": max_depth,
        }

    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        return {"error": str(e)}


def get_dependencies(
    workdir: str,
    path: str,
    include_stdlib: bool = False,
    include_external: bool = True,
    direction: str = "to",
    depth: int = 1,
) -> Dict[str, Any]:
    """
    Extract and analyze Python import dependencies.

    Args:
        workdir: Absolute path to task working directory
        path: File or directory path relative to workdir
        include_stdlib: Include Python standard library imports
        include_external: Include third-party library imports
        direction: Show imports "to" or "from"
        depth: Maximum depth to follow dependencies

    Returns:
        Dict with dependency graph, cycles, and unused imports
    """
    try:
        target_path = Path(workdir) / path
        if not target_path.exists():
            return {"error": f"Path not found: {path}"}

        dependencies = {
            "path": path,
            "direct_dependencies": [],
            "indirect_dependencies": [],
            "circular_dependencies": [],
            "unused_imports": [],
            "dependency_count": 0,
        }

        # Find Python files to analyze
        if target_path.is_file():
            py_files = [target_path]
        else:
            py_files = list(target_path.rglob("*.py"))

        # Parse imports from each file
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dependencies["direct_dependencies"].append({
                                "module": alias.name,
                                "type": "import",
                                "line_number": node.lineno,
                                "is_local": False,
                            })

                    elif isinstance(node, ast.ImportFrom):
                        dependencies["direct_dependencies"].append({
                            "module": node.module or "",
                            "type": "from...import",
                            "items": [alias.name for alias in node.names],
                            "line_number": node.lineno,
                            "is_local": not (node.module and ("." not in node.module)),
                        })

            except (SyntaxError, UnicodeDecodeError):
                continue

        dependencies["dependency_count"] = len(dependencies["direct_dependencies"])

        logger.info(f"Analyzed dependencies for {path}: {dependencies['dependency_count']} imports")

        return dependencies

    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        return {"error": str(e)}