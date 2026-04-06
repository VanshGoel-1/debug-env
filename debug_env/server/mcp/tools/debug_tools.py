"""
Debug Tools Module

Comprehensive set of tools for advanced code debugging and analysis.
Provides code search, structure analysis, type checking, coverage analysis, and dependency inspection.
"""

DEBUG_TOOLS = [
    {
        "name": "search_code",
        "description": """Search for code patterns across files in the task directory.

        Searches for text or regex patterns across source files, useful for locating
        where functions are called, variable usage, or specific error patterns.
        Similar to grep/rg operations but integrated for debugging workflow.

        Required Parameters:
          - pattern: Text or regex pattern to search for (case-insensitive by default)
          - file_types: Optional. Filter by file type (default: "py" for Python files only)
                        Enum: "py" (Python), "all" (all files), "txt", "json", etc.

        Optional Parameters:
          - case_sensitive: Whether to match case (default: false)
          - max_results: Maximum number of matches to return (default: 50, max: 500)
          - context_lines: Lines of context around each match (default: 2, max: 10)

        Search Behavior:
          - Returns matches with line numbers, filenames, and surrounding context
          - Sorted by filename then line number
          - If pattern contains regex special chars, it's treated as regex
          - Matches are highlighted with context for easy reading
          - Path traversal protection: only searches within task directory

        Response Structure:
          - matches: Array of match objects, each containing:
            * filename: File containing the match
            * line_number: Line number (1-indexed)
            * line_content: The matching line
            * before: Context lines before (array)
            * after: Context lines after (array)
            * match_position: Column where match starts
          - total_matches: Total number of matches found
          - files_searched: Number of files examined
          - search_time_ms: Search execution time

        Status Codes:
          - 200: Success - Search completed (may have 0 matches)
          - 400: Bad Request - Invalid pattern or parameters
          - 500: Internal Server Error
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text or regex pattern to search for",
                    "minLength": 1,
                    "maxLength": 500,
                },
                "file_types": {
                    "type": "string",
                    "description": "File type filter (py, all, txt, json, etc.)",
                    "enum": ["py", "all", "txt", "json", "md"],
                    "default": "py",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether to match case",
                    "default": False,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matches to return",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 50,
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Lines of context around each match",
                    "minimum": 0,
                    "maximum": 10,
                    "default": 2,
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "get_file_structure",
        "description": """Parse and return the structure (AST) of a Python file.

        Analyzes the Abstract Syntax Tree of a Python file to extract functions,
        classes, methods, imports, and their locations. Useful for understanding
        code organization before editing.

        Required Parameters:
          - path: File path relative to task directory (e.g., 'broken_code.py')

        Optional Parameters:
          - include_docstrings: Include docstrings in output (default: true)
          - include_signatures: Include function/method signatures (default: true)
          - max_depth: Maximum nesting depth to analyze (default: unlimited)

        Structure Analysis:
          - Extracts top-level functions and classes
          - For each class: lists methods, attributes, parent classes
          - For each function: shows parameters, return type hint (if present)
          - Shows decorators (@property, @staticmethod, etc.)
          - Identifies imports (from/import statements)
          - Groups by section (imports, classes, functions, constants)

        Response Structure:
          - filename: The analyzed file
          - imports: Array of import statements with line numbers
            * module: Imported module
            * items: What was imported (function/class/constant names)
            * line_number: Where imported
          - classes: Array of class definitions
            * name: Class name
            * line_number: Definition line
            * methods: Array of method names with line numbers
            * attributes: Instance attributes with types (if annotated)
            * docstring: Class docstring (if present)
          - functions: Array of top-level functions
            * name: Function name
            * line_number: Definition line
            * parameters: Param names and types (if annotated)
            * return_type: Return type hint (if present)
            * docstring: Function docstring (if present)
          - constants: Module-level constants
            * name: Constant name
            * line_number: Definition line
            * value: Literal value (if simple)

        Status Codes:
          - 200: Success - File structure extracted
          - 400: Bad Request - Invalid Python syntax or file not found
          - 500: Internal Server Error
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to task directory",
                    "minLength": 1,
                    "maxLength": 255,
                },
                "include_docstrings": {
                    "type": "boolean",
                    "description": "Include docstrings in output",
                    "default": True,
                },
                "include_signatures": {
                    "type": "boolean",
                    "description": "Include function/method signatures",
                    "default": True,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum nesting depth to analyze (0 for unlimited)",
                    "minimum": 0,
                    "default": 0,
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_type_check",
        "description": """Run static type checking (mypy) on Python files.

        Executes mypy type checker on specified file or directory to identify
        type errors, missing annotations, and type incompatibilities.
        Useful for catching type-related bugs before runtime.

        Required Parameters:
          - path: File or directory path relative to task directory
                  (e.g., 'broken_code.py' or '.')

        Optional Parameters:
          - strict: Enable strict mode (all optional checks, default: false)
          - ignore_missing_imports: Ignore errors from untyped libraries (default: true)
          - show_error_codes: Show error codes in output (default: true)
          - max_errors: Maximum errors to report (default: 100)

        Type Check Behavior:
          - Analyzes type annotations and infers types
          - Reports missing type hints where inferred types conflict
          - Checks function argument types against signatures
          - Validates attribute access on typed objects
          - Catches common type errors (None checks, incompatible operations)
          - Produces detailed error messages with suggestions

        Response Structure:
          - path: File/directory analyzed
          - status: "success" or "errors_found"
          - error_count: Total number of type errors
          - errors: Array of error objects
            * file: File containing error
            * line: Line number (1-indexed)
            * column: Column number (1-indexed)
            * message: Detailed error message
            * error_code: mypy error code (e.g., "var-annotated")
            * suggestion: Suggested fix (if available)
          - success_count: Number of successfully type-checked items
          - check_time_ms: Type check execution time

        Status Codes:
          - 200: Success - Type check completed (may report errors)
          - 400: Bad Request - Invalid path or mypy configuration
          - 500: Internal Server Error
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File or directory path relative to task directory",
                    "minLength": 1,
                    "maxLength": 255,
                },
                "strict": {
                    "type": "boolean",
                    "description": "Enable strict type checking mode",
                    "default": False,
                },
                "ignore_missing_imports": {
                    "type": "boolean",
                    "description": "Ignore errors from untyped third-party libraries",
                    "default": True,
                },
                "show_error_codes": {
                    "type": "boolean",
                    "description": "Show mypy error codes in output",
                    "default": True,
                },
                "max_errors": {
                    "type": "integer",
                    "description": "Maximum errors to report before stopping",
                    "minimum": 1,
                    "maximum": 500,
                    "default": 100,
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_test_coverage",
        "description": """Analyze test coverage for Python files.

        Runs coverage.py to measure which lines of code are executed by tests.
        Shows coverage percentage per file/function, identifying untested code paths.
        Useful for understanding test completeness and finding missing edge cases.

        Required Parameters:
          - path: File or directory path relative to task directory (optional, default: '.')

        Optional Parameters:
          - branch_coverage: Include branch coverage (if/else paths, default: false)
          - include_missing: Show which lines are not covered (default: true)
          - fail_under: Minimum coverage % required (0-100, default: 0)

        Coverage Behavior:
          - Runs test suite and tracks line execution
          - Shows coverage for each file
          - Shows coverage for each function/class
          - Identifies completely uncovered functions/methods
          - Can detect dead code (0% coverage)
          - Branch coverage shows if/else branches taken

        Response Structure:
          - total_coverage: Overall coverage percentage (0-100)
          - files: Array of file coverage objects
            * filename: File path
            * coverage: Coverage percentage
            * lines_total: Total executable lines
            * lines_covered: Lines executed by tests
            * missing_lines: Array of uncovered line numbers (if include_missing)
          - functions: Array of function coverage objects
            * name: Function name
            * file: File containing function
            * coverage: Coverage percentage (0 or 100 for line coverage)
            * line_number: Function definition line
          - status: "covered", "partially_covered", or "uncovered" based on fail_under
          - check_time_ms: Coverage analysis time

        Status Codes:
          - 200: Success - Coverage analyzed
          - 400: Bad Request - Invalid path or coverage configuration
          - 500: Internal Server Error
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File or directory path relative to task directory",
                    "minLength": 1,
                    "maxLength": 255,
                    "default": ".",
                },
                "branch_coverage": {
                    "type": "boolean",
                    "description": "Include branch (if/else) coverage analysis",
                    "default": False,
                },
                "include_missing": {
                    "type": "boolean",
                    "description": "Show which lines are not covered",
                    "default": True,
                },
                "fail_under": {
                    "type": "integer",
                    "description": "Minimum required coverage percentage (0-100)",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "list_directory",
        "description": """List files and directories in the task working directory.

        Returns a directory tree showing file structure, sizes, types, and metadata.
        Useful for understanding what files exist and their organization before
        starting to debug or edit code.

        Required Parameters: None (default: current task directory)

        Optional Parameters:
          - path: Subdirectory path relative to task root (default: '.')
          - recursive: Include subdirectories recursively (default: true)
          - max_depth: Maximum directory nesting depth (default: unlimited)
          - include_hidden: Include hidden files/folders starting with . (default: false)
          - file_types: Filter by file type (py, all, test, etc.)

        Directory Listing:
          - Shows files and folders in hierarchical structure
          - Includes file size in bytes
          - Shows file type/extension
          - Marks executable files
          - Marks test files separately
          - Indicates if file is readable/writable

        Response Structure:
          - root_path: Base directory path
          - total_files: Total number of files (excluding directories)
          - total_directories: Total number of subdirectories
          - items: Array of directory entry objects
            * name: File or directory name
            * type: "file" or "directory"
            * path: Full path relative to task root
            * size_bytes: File size in bytes (for files)
            * is_test: Whether file matches test pattern (test_*.py)
            * is_executable: Whether file is executable
            * contents: Array of child items (for directories if recursive)
          - tree_depth: Maximum nesting depth found

        Status Codes:
          - 200: Success - Directory listed
          - 404: Not Found - Directory path does not exist
          - 500: Internal Server Error
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Subdirectory path relative to task root",
                    "default": ".",
                    "maxLength": 255,
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Include subdirectories recursively",
                    "default": True,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory nesting depth (0 for unlimited)",
                    "minimum": 0,
                    "default": 0,
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files/folders starting with .",
                    "default": False,
                },
                "file_types": {
                    "type": "string",
                    "description": "Filter by file type",
                    "enum": ["py", "all", "test", "source"],
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_dependencies",
        "description": """Extract and analyze Python import dependencies.

        Parses import statements to build a dependency graph showing what modules/files
        depend on each other. Useful for understanding code relationships and identifying
        circular dependencies or unexpected coupling.

        Required Parameters:
          - path: File or directory path relative to task directory (e.g., 'broken_code.py' or '.')

        Optional Parameters:
          - include_stdlib: Include Python standard library imports (default: false)
          - include_external: Include third-party library imports (default: true)
          - direction: Show imports "to" (what this imports) or "from" (what imports this)
                       (default: "to")
          - depth: Maximum depth to follow dependencies (default: 1)

        Dependency Analysis:
          - Extracts all import statements (import x, from x import y)
          - Categorizes imports (local, stdlib, external)
          - Builds dependency graph showing import relationships
          - Detects circular dependencies (A imports B, B imports A)
          - Shows unused imports
          - Maps relative imports to absolute module paths

        Response Structure:
          - path: File or directory analyzed
          - direct_dependencies: Array of direct imports
            * module: Module being imported
            * type: "import" or "from...import"
            * items: What was imported (if from...import)
            * source_file: File being imported FROM (if local import)
            * is_local: Whether importing from task code
            * line_number: Import statement line number
          - indirect_dependencies: Array of transitive dependencies (if depth > 1)
            * module: Module name
            * via: Path showing how it's imported
            * chain_length: Number of imports deep
          - circular_dependencies: Array of detected cycles
            * cycle: Array of module names forming cycle
            * files: File paths involved in cycle
          - unused_imports: Imports that appear to be unused
            * module: Imported but never referenced
            * file: File with unused import
            * line_number: Import location
          - dependency_count: Total number of dependencies

        Status Codes:
          - 200: Success - Dependencies extracted
          - 400: Bad Request - Invalid path or syntax error in files
          - 500: Internal Server Error
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File or directory path relative to task directory",
                    "minLength": 1,
                    "maxLength": 255,
                },
                "include_stdlib": {
                    "type": "boolean",
                    "description": "Include Python standard library imports",
                    "default": False,
                },
                "include_external": {
                    "type": "boolean",
                    "description": "Include third-party library imports",
                    "default": True,
                },
                "direction": {
                    "type": "string",
                    "description": "Show imports 'to' (what this imports) or 'from' (what imports this)",
                    "enum": ["to", "from"],
                    "default": "to",
                },
                "depth": {
                    "type": "integer",
                    "description": "Maximum depth to follow dependencies",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1,
                },
            },
            "required": ["path"],
        },
    },
]