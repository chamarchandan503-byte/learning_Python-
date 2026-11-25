"""Comprehensive unit tests for the To-Do List Manager package."""

from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import main
import todo
from models import Task, normalize_priority, normalize_tags, validate_due_date
from storage import (
    export_tasks_to_csv,
    get_backup_path,
    load_tasks_data,
    restore_from_backup,
    save_tasks_data,
)
from todo import TodoManager


class TestModels(unittest.TestCase):
    def test_legacy_record_migration_defaults(self) -> None:
        task = Task.from_dict({"id": 1, "title": "Buy milk", "completed": False})
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Buy milk")
        self.assertFalse(task.completed)
        self.assertEqual(task.priority, "Medium")
        self.assertEqual(task.category, "General")
        self.assertIsNone(task.due_date)
        self.assertEqual(task.tags, [])
        self.assertIsNone(task.completed_at)

    def test_priority_and_tag_normalization(self) -> None:
        self.assertEqual(normalize_priority("u"), "Urgent")
        self.assertEqual(normalize_priority("HIGH"), "High")
        self.assertEqual(normalize_priority(""), "Medium")
        with self.assertRaises(ValueError):
            normalize_priority("critical")

        self.assertEqual(
            normalize_tags("work, Python, work, Urgent "),
            ["work", "Python", "Urgent"],
        )

    def test_due_date_validation_and_overdue_logic(self) -> None:
        self.assertEqual(validate_due_date("2026-12-01"), "2026-12-01")
        self.assertIsNone(validate_due_date("  "))
        with self.assertRaises(ValueError):
            validate_due_date("01-12-2026")

        overdue_task = Task(id=1, title="Pay bill", due_date="2026-11-20")
        self.assertTrue(overdue_task.is_overdue(reference_date=date(2026, 11, 25)))
        self.assertEqual(overdue_task.days_remaining(reference_date=date(2026, 11, 25)), -5)

        overdue_task.mark_completed()
        self.assertFalse(overdue_task.is_overdue(reference_date=date(2026, 11, 25)))
        self.assertIsNotNone(overdue_task.completed_at)


class TestStorage(unittest.TestCase):
    def test_atomic_save_backup_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "tasks.json"
            first = [Task(id=1, title="First task").to_dict()]
            save_tasks_data(first, data_file=data_file)

            second = first + [Task(id=2, title="Second task", priority="High").to_dict()]
            save_tasks_data(second, data_file=data_file)

            backup_file = get_backup_path(data_file)
            self.assertTrue(backup_file.exists())
            self.assertEqual(len(load_tasks_data(data_file)), 2)
            self.assertEqual(len(load_tasks_data(backup_file)), 1)

            # Corrupt primary file and recover from backup
            data_file.write_text("{corrupt json", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                load_tasks_data(data_file)

            restored = restore_from_backup(data_file)
            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0]["title"], "First task")

    def test_duplicate_ids_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "tasks.json"
            payload = [
                {"id": 1, "title": "A", "completed": False},
                {"id": 1, "title": "B", "completed": True},
            ]
            data_file.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                load_tasks_data(data_file)

    def test_export_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "export.csv"
            tasks = [
                Task(
                    id=1,
                    title="Write tests",
                    priority="High",
                    category="Dev",
                    tags=["python", "qa"],
                    due_date="2026-12-10",
                ).to_dict()
            ]
            export_tasks_to_csv(tasks, csv_path)
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Write tests")
            self.assertEqual(rows[0]["tags"], "python, qa")


class TestTodoManagerAndProceduralAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.tmp_dir.name) / "tasks.json"
        self.manager = TodoManager(data_file=self.data_file)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_crud_complete_reopen_and_undo(self) -> None:
        t1 = self.manager.add_task(
            title="Build API",
            description="Implement endpoints",
            priority="High",
            category="Work",
            due_date="2026-11-30",
            tags="backend, python",
        )
        t2 = self.manager.add_task(title="Read book", priority="Low", category="Personal")
        self.assertEqual(t1["id"], 1)
        self.assertEqual(t2["id"], 2)

        edited = self.manager.edit_task(1, title="Build REST API", priority="Urgent", due_date="2026-11-28")
        self.assertEqual(edited["title"], "Build REST API")
        self.assertEqual(edited["priority"], "Urgent")
        self.assertEqual(edited["due_date"], "2026-11-28")

        self.assertTrue(self.manager.complete_task(1))
        self.assertFalse(self.manager.complete_task(1))
        self.assertTrue(self.manager.get_task(1)["completed"])  # type: ignore[index]

        self.assertTrue(self.manager.reopen_task(1))
        self.assertFalse(self.manager.get_task(1)["completed"])  # type: ignore[index]

        # Undo reopen -> task 1 should be completed again
        self.assertTrue(self.manager.undo())
        self.assertTrue(self.manager.get_task(1)["completed"])  # type: ignore[index]

        removed_count = self.manager.clear_completed()
        self.assertEqual(removed_count, 1)
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertEqual(self.manager.tasks[0]["id"], 2)

        # Undo clear_completed -> both tasks back
        self.assertTrue(self.manager.undo())
        self.assertEqual(len(self.manager.tasks), 2)

    def test_search_filter_sort_and_statistics(self) -> None:
        self.manager.add_task(
            title="Fix login bug",
            priority="Urgent",
            category="Work",
            due_date="2026-11-20",
            tags="security",
        )
        self.manager.add_task(
            title="Buy groceries",
            priority="Medium",
            category="Home",
            due_date="2026-11-25",
            tags="errand",
        )
        self.manager.add_task(
            title="Archive old notes",
            priority="Low",
            category="Work",
        )
        self.manager.complete_task(3)

        self.assertEqual(len(self.manager.search("security")), 1)
        self.assertEqual(len(self.manager.search("Work")), 2)

        ref = date(2026, 11, 25)
        overdue = self.manager.filter(overdue_only=True, reference_date=ref)
        self.assertEqual([t["id"] for t in overdue], [1])

        pending_work = self.manager.filter(status="pending", category="work")
        self.assertEqual([t["id"] for t in pending_work], [1])

        by_priority = self.manager.sort(by="priority", descending=True)
        self.assertEqual([t["id"] for t in by_priority], [1, 2, 3])

        by_due = self.manager.sort(by="due_date")
        self.assertEqual([t["id"] for t in by_due], [1, 2, 3])

        stats = self.manager.get_statistics(reference_date=ref)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["pending"], 2)
        self.assertEqual(stats["overdue_count"], 1)
        self.assertEqual(stats["due_today_count"], 1)
        self.assertEqual(stats["completion_rate"], 33.3)

    def test_procedural_backward_compatible_functions(self) -> None:
        tasks = todo.load_tasks(self.data_file)
        with redirect_stdout(io.StringIO()):
            created = todo.add_task(tasks, "Legacy call", data_file=self.data_file)
            self.assertIsNotNone(created)
            self.assertTrue(todo.complete_task(tasks, 1, data_file=self.data_file))
            todo.view_tasks(tasks)
            self.assertTrue(todo.delete_task(tasks, 1, data_file=self.data_file))
        self.assertEqual(todo.load_tasks(self.data_file), [])


class TestCLISmoke(unittest.TestCase):
    def test_cli_add_view_and_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "tasks.json"
            inputs = iter(
                [
                    "1",          # Add New Task
                    "CLI Task",   # title
                    "Details",    # description
                    "High",       # priority
                    "Study",      # category
                    "2026-12-31", # due date
                    "cli, test",  # tags
                    "2",          # View All Tasks
                    "10",         # Dashboard
                    "0",          # Exit
                ]
            )
            buffer = io.StringIO()
            with patch("builtins.input", lambda _prompt="": next(inputs)), redirect_stdout(buffer):
                main.run_app(data_file=data_file)

            output = buffer.getvalue()
            self.assertIn("CLI Task", output)
            self.assertIn("PRODUCTIVITY DASHBOARD", output)
            saved = load_tasks_data(data_file)
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["priority"], "High")


if __name__ == "__main__":
    unittest.main(verbosity=2)
