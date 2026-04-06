"""
TaskLoader — copies task source files into a fresh temp directory for each episode.

Task layout on disk:
    debug_env/tasks/
        task1/
            broken_code.py
            test_code.py
        task2/
            broken_code.py
            test_code.py
        task3/
            broken_code.py
            helper.py
            test_code.py
"""

import shutil
import tempfile
from pathlib import Path

from debug_env.server.tasks.data import get_available_task_ids, validate_task_id

TASKS_DIR = Path(__file__).parent.parent.parent / "tasks"


class TaskLoader:
    """Manages task file staging into isolated temp directories."""

    @staticmethod
    def available_tasks() -> list[str]:
        """Return sorted list of registered task IDs."""
        return get_available_task_ids()

    @staticmethod
    def load(task_id: str, previous_workdir: str | None = None) -> str:
        """
        Copy all files for *task_id* into a fresh temp directory.
        For tasks with seed data, generates files from seed data.

        Args:
            task_id:           e.g. "task1"
            previous_workdir:  if provided, this directory is deleted first.

        Returns:
            Path to the new workdir (str).

        Raises:
            ValueError: if task_id is not in the registry.
            FileNotFoundError: if task files are missing from disk.
        """
        if not validate_task_id(task_id):
            available = get_available_task_ids()
            raise ValueError(
                f"Unknown task '{task_id}'. Available: {available}"
            )

        if previous_workdir:
            shutil.rmtree(previous_workdir, ignore_errors=True)

        workdir = tempfile.mkdtemp(prefix=f"debug_{task_id}_")

        # For tasks with seed data, generate files from seed data
        if task_id == "task4":
            TaskLoader._generate_task4_files(workdir)
        elif task_id == "task5":
            TaskLoader._generate_task5_files(workdir)
        elif task_id == "task6":
            TaskLoader._generate_task6_files(workdir)
        elif task_id == "task7":
            TaskLoader._generate_task7_files(workdir)
        elif task_id == "task8":
            TaskLoader._generate_task8_files(workdir)
        elif task_id == "task9":
            TaskLoader._generate_task9_files(workdir)
        else:
            # For other tasks, copy from disk
            task_path = TASKS_DIR / task_id
            if not task_path.is_dir():
                raise FileNotFoundError(
                    f"Task files for '{task_id}' not found on disk at {task_path}"
                )

            for f in task_path.iterdir():
                if f.is_file():
                    shutil.copy2(f, workdir)

        return workdir

    @staticmethod
    def _generate_task4_files(workdir: str) -> None:
        """Generate task4 files from seed data."""
        from debug_env.tasks.task4.seed_data import (
            get_task4_seed_data,
            get_test_file_content,
        )

        seed = get_task4_seed_data()
        for filename, content in seed["files"].items():
            filepath = Path(workdir) / filename
            filepath.write_text(content, encoding="utf-8")

        # Write test file
        test_content = get_test_file_content()
        (Path(workdir) / seed["test_file"]).write_text(test_content, encoding="utf-8")

    @staticmethod
    def _generate_task5_files(workdir: str) -> None:
        """Generate task5 files from seed data."""
        from debug_env.tasks.task5.seed_data import (
            get_task5_seed_data,
            get_test_file_content,
        )

        seed = get_task5_seed_data()
        for filename, content in seed["files"].items():
            filepath = Path(workdir) / filename
            filepath.write_text(content, encoding="utf-8")

        # Write test file
        test_content = get_test_file_content()
        (Path(workdir) / seed["test_file"]).write_text(test_content, encoding="utf-8")

    @staticmethod
    def _generate_task6_files(workdir: str) -> None:
        """Generate task6 files from seed data."""
        from debug_env.tasks.task6.seed_data import (
            get_task6_seed_data,
            get_test_file_content,
        )

        seed = get_task6_seed_data()
        for filename, content in seed["files"].items():
            filepath = Path(workdir) / filename
            filepath.write_text(content, encoding="utf-8")

        # Write test file
        test_content = get_test_file_content()
        (Path(workdir) / seed["test_file"]).write_text(test_content, encoding="utf-8")

    @staticmethod
    def _generate_task7_files(workdir: str) -> None:
        """Generate task7 files from seed data."""
        from debug_env.tasks.task7.seed_data import (
            get_task7_seed_data,
            get_test_auth_py_content,
        )

        seed = get_task7_seed_data()
        for filename, content in seed["files"].items():
            filepath = Path(workdir) / filename
            filepath.write_text(content, encoding="utf-8")

        # Write test file
        test_content = get_test_auth_py_content()
        (Path(workdir) / seed["test_file"]).write_text(test_content, encoding="utf-8")

    @staticmethod
    def _generate_task8_files(workdir: str) -> None:
        """Generate task8 files from seed data."""
        from debug_env.tasks.task8.seed_data import (
            get_task8_seed_data,
            get_test_user_service_content,
        )

        seed = get_task8_seed_data()
        for filename, content in seed["files"].items():
            filepath = Path(workdir) / filename
            filepath.write_text(content, encoding="utf-8")

        # Write test file
        test_content = get_test_user_service_content()
        (Path(workdir) / seed["test_file"]).write_text(test_content, encoding="utf-8")

    @staticmethod
    def _generate_task9_files(workdir: str) -> None:
        """Generate task9 files from seed data."""
        from debug_env.tasks.task9.seed_data import (
            get_task9_seed_data,
            get_test_file_content,
        )

        seed = get_task9_seed_data()
        for filename, content in seed["files"].items():
            filepath = Path(workdir) / filename
            filepath.write_text(content, encoding="utf-8")

        # Write test file
        test_content = get_test_file_content()
        (Path(workdir) / seed["test_file"]).write_text(test_content, encoding="utf-8")

    @staticmethod
    def list_source_files(task_id: str) -> list[str]:
        """
        Return the editable source filenames for a task (excludes test files).

        Args:
            task_id: e.g. "task1"

        Returns:
            Sorted list of filenames, e.g. ["broken_code.py"]

        Raises:
            ValueError: if task_id is not registered.
        """
        if not validate_task_id(task_id):
            raise ValueError(f"Unknown task '{task_id}'.")
        task_path = TASKS_DIR / task_id
        return sorted(
            f.name for f in task_path.iterdir()
            if f.is_file() and not f.name.startswith("test_")
        )

    @staticmethod
    def read_source_file(task_id: str, filename: str) -> str:
        """
        Read the canonical (pre-episode) content of a source file.

        Args:
            task_id:  e.g. "task1"
            filename: e.g. "broken_code.py"

        Returns:
            File content as a string.

        Raises:
            ValueError: if task_id is not registered or filename is invalid.
            FileNotFoundError: if the file does not exist on disk.
        """
        if not validate_task_id(task_id):
            raise ValueError(f"Unknown task '{task_id}'.")
        if ".." in filename or filename.startswith("/"):
            raise ValueError(f"Invalid filename '{filename}'.")
        file_path = TASKS_DIR / task_id / filename
        if not file_path.is_file():
            available = TaskLoader.list_source_files(task_id)
            raise FileNotFoundError(
                f"File '{filename}' not found in task '{task_id}'. "
                f"Available source files: {available}"
            )
        return file_path.read_text(encoding="utf-8")
