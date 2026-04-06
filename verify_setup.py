#!/usr/bin/env python
"""
Verification script for OpenEnv Competition Setup

Checks all required components and validates the setup is ready for submission.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_file_exists(path: str, description: str) -> Tuple[bool, str]:
    """Check if a required file exists."""
    p = Path(path)
    if p.exists():
        return True, f"[OK] {description}: {path}"
    return False, f"[FAIL] {description}: MISSING - {path}"

def check_python_module(module_name: str) -> Tuple[bool, str]:
    """Check if a Python module is installed."""
    try:
        __import__(module_name)
        return True, f"[OK] {module_name} installed"
    except ImportError:
        return False, f"[FAIL] {module_name} NOT installed"

def check_env_var(var_name: str) -> Tuple[bool, str]:
    """Check if an environment variable is set."""
    value = os.getenv(var_name)
    if value:
        masked = value[:10] + "***" if len(value) > 10 else "***"
        return True, f"[OK] {var_name} is set ({masked})"
    return False, f"[FAIL] {var_name} NOT set"

def check_syntax(file_path: str) -> Tuple[bool, str]:
    """Check Python file syntax."""
    try:
        compile(open(file_path).read(), file_path, 'exec')
        return True, f"[OK] {file_path} syntax OK"
    except SyntaxError as e:
        return False, f"[FAIL] {file_path} has syntax error: {e}"

def check_task_files() -> Tuple[bool, str]:
    """Check that all tasks have required files."""
    for task_num in [1, 2, 3]:
        task_dir = f"debug_env/tasks/task{task_num}"
        broken_code = f"{task_dir}/broken_code.py"
        test_code = f"{task_dir}/test_code.py"

        if not Path(broken_code).exists():
            return False, f"[FAIL] {broken_code} missing"
        if not Path(test_code).exists():
            return False, f"[FAIL] {test_code} missing"

    return True, "[OK] All 3 tasks have required files"

def check_docker_file() -> Tuple[bool, str]:
    """Check Dockerfile exists and is readable."""
    dockerfile = "debug_env/server/Dockerfile"
    if Path(dockerfile).exists():
        try:
            with open(dockerfile) as f:
                content = f.read()
                if "FROM" in content and "CMD" in content:
                    return True, f"[OK] Dockerfile is valid"
        except Exception as e:
            return False, f"[FAIL] Dockerfile error: {e}"
    return False, f"[FAIL] Dockerfile missing"

def main():
    print("\n" + "=" * 70)
    print("OpenEnv Competition Setup Verification")
    print("=" * 70 + "\n")

    checks = []

    # 1. File structure
    print("1. Checking file structure...")
    checks.append(check_file_exists("debug_env/openenv.yaml", "openenv.yaml"))
    checks.append(check_file_exists("inference.py", "inference.py (competition entry point)"))
    checks.append(check_file_exists(".env", ".env configuration"))
    checks.append(check_file_exists(".env.example", ".env.example template"))
    checks.append(check_file_exists("README.md", "README.md"))
    checks.append(check_file_exists("QUICKSTART.md", "QUICKSTART.md"))
    checks.append(check_file_exists("COMPETITION_CHECKLIST.md", "COMPETITION_CHECKLIST.md"))
    checks.append(check_file_exists("pyproject.toml", "pyproject.toml (root)"))
    checks.append(check_file_exists("docker-compose.yml", "docker-compose.yml"))
    checks.append(check_docker_file())

    # 2. Task files
    print("\n2. Checking task files...")
    checks.append(check_task_files())

    # 3. Python syntax
    print("\n3. Checking Python syntax...")
    checks.append(check_syntax("inference.py"))

    # 4. Required Python modules
    print("\n4. Checking Python dependencies...")
    checks.append(check_python_module("openai"))
    checks.append(check_python_module("httpx"))
    checks.append(check_python_module("openenv"))
    checks.append(check_python_module("fastapi"))

    # 5. Environment variables
    print("\n5. Checking environment configuration...")
    checks.append(check_env_var("OPENAI_API_KEY"))
    checks.append(check_env_var("API_BASE_URL"))
    checks.append(check_env_var("MODEL_NAME"))

    # Print results
    print("\n" + "=" * 70)
    print("Verification Results")
    print("=" * 70 + "\n")

    passed = 0
    failed = 0

    for success, message in checks:
        print(message)
        if success:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"Summary: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    if failed == 0:
        print("[SUCCESS] All checks passed! Your setup is ready for competition.\n")
        print("Next steps:")
        print("  1. Set OPENAI_API_KEY in .env with your actual API key")
        print("  2. Run: python inference.py")
        print("  3. Check results in results_task1_*.json")
        print("  4. Deploy to Hugging Face Spaces")
        return 0
    else:
        print(f"[ERROR] {failed} checks failed. Please fix the issues above.\n")
        if failed >= 2:
            print("Start with:")
            print("  1. pip install -e .")
            print("  2. cp .env.example .env")
            print("  3. Edit .env with your OPENAI_API_KEY")
        return 1

if __name__ == "__main__":
    sys.exit(main())
