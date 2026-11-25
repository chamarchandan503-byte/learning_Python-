"""Core business logic and task management operations for the To-Do List app."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

from models import (
    PRIORITY_WEIGHTS,
    VALID_PRIORITIES,
    Task,
    normalize_priority,
    normalize_tags,
    now_timestamp,
    validate_due_date,
)
from storage import (
    DEFAULT_DATA_FILE,
    export_tasks_to_csv,
    load_tasks_data,
    restore_from_backup,
    save_tasks_data,
)

DATA_FILE = DEFAULT_DATA_FILE
MAX_UNDO_HISTORY = 25


class TodoManager:
    """Manages tasks, persistence, search/filtering, statistics, and undo history."""

    def __init__(self, data_file: Path = DEFAULT_DATA_FILE, auto_load: bool = True) -> None:
        self.data_file = Path(data_file)
        self.tasks: list[dict[str, Any]] = []
        self._undo_stack: list[list[dict[str, Any]]] = []
        if auto_load:
            self.load()

    @property
    def can_undo(self) -> bool:
        """Return True if at least one previous state snapshot is available."""
        return len(self._undo_stack) > 0

    def _push_history(self) -> None:
        """Save a deep copy of current tasks before a mutating operation."""
        self._undo_stack.append(deepcopy(self.tasks))
        if len(self._undo_stack) > MAX_UNDO_HISTORY:
            self._undo_stack.pop(0)

    def load(self) -> list[dict[str, Any]]:
        """Load tasks from storage into memory."""
        self.tasks = load_tasks_data(self.data_file)
        self._undo_stack.clear()
        return self.tasks

    def save(self, create_backup: bool = True) -> None:
        """Persist current tasks to storage atomically."""
        save_tasks_data(self.tasks, data_file=self.data_file, create_backup=create_backup)

    def undo(self) -> bool:
        """Revert the last mutating operation and persist the restored state."""
        if not self._undo_stack:
            return False
        self.tasks = self._undo_stack.pop()
        self.save(create_backup=False)
        return True

    def restore_backup(self) -> list[dict[str, Any]]:
        """Restore tasks from backup storage and update in-memory state."""
        self._push_history()
        try:
            self.tasks = restore_from_backup(self.data_file)
        except Exception:
            self._undo_stack.pop()
            raise
        return self.tasks

    def _find_index(self, task_id: int) -> int:
        for index, task in enumerate(self.tasks):
            if task["id"] == task_id:
                return index
        raise KeyError(f"Task ID {task_id} not found.")

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        """Return a task dictionary by ID, or None if not found."""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def next_id(self) -> int:
        """Generate the next sequential task ID."""
        return max((task["id"] for task in self.tasks), default=0) + 1

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "Medium",
        category: str = "General",
        due_date: str | None = None,
        tags: list[str] | str | None = None,
    ) -> dict[str, Any]:
        """Create, validate, persist, and return a new task."""
        task = Task(
            id=self.next_id(),
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
            tags=normalize_tags(tags),
        )
        record = task.to_dict()
        self._push_history()
        self.tasks.append(record)
        try:
            self.save()
        except Exception:
            self.tasks.pop()
            self._undo_stack.pop()
            raise
        return record

    def edit_task(
        self,
        task_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        due_date: str | None = ...,  # type: ignore[assignment]
        tags: list[str] | str | None = None,
    ) -> dict[str, Any]:
        """Update selected fields of an existing task and save."""
        idx = self._find_index(task_id)
        current = deepcopy(self.tasks[idx])

        if title is not None:
            cleaned_title = title.strip()
            if not cleaned_title:
                raise ValueError("Task title cannot be empty.")
            current["title"] = cleaned_title

        if description is not None:
            current["description"] = description.strip()

        if priority is not None:
            current["priority"] = normalize_priority(priority)

        if category is not None:
            cleaned_category = category.strip()
            current["category"] = cleaned_category if cleaned_category else "General"

        if due_date is not ...:
            current["due_date"] = validate_due_date(due_date)

        if tags is not None:
            current["tags"] = normalize_tags(tags)

        current["updated_at"] = now_timestamp()
        validated = Task.from_dict(current).to_dict()

        self._push_history()
        self.tasks[idx] = validated
        try:
            self.save()
        except Exception:
            self.tasks = self._undo_stack.pop()
            raise
        return validated

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed. Returns False if it was already completed."""
        idx = self._find_index(task_id)
        if self.tasks[idx]["completed"]:
            return False

        task = Task.from_dict(self.tasks[idx])
        task.mark_completed()
        self._push_history()
        self.tasks[idx] = task.to_dict()
        try:
            self.save()
        except Exception:
            self.tasks = self._undo_stack.pop()
            raise
        return True

    def reopen_task(self, task_id: int) -> bool:
        """Reopen a completed task. Returns False if it was already pending."""
        idx = self._find_index(task_id)
        if not self.tasks[idx]["completed"]:
            return False

        task = Task.from_dict(self.tasks[idx])
        task.reopen()
        self._push_history()
        self.tasks[idx] = task.to_dict()
        try:
            self.save()
        except Exception:
            self.tasks = self._undo_stack.pop()
            raise
        return True

    def delete_task(self, task_id: int) -> dict[str, Any]:
        """Delete a task by ID and return the deleted record."""
        idx = self._find_index(task_id)
        self._push_history()
        removed = self.tasks.pop(idx)
        try:
            self.save()
        except Exception:
            self.tasks = self._undo_stack.pop()
            raise
        return removed

    def clear_completed(self) -> int:
        """Remove all completed tasks and return the number of deleted tasks."""
        completed_count = sum(1 for task in self.tasks if task["completed"])
        if completed_count == 0:
            return 0

        self._push_history()
        self.tasks = [task for task in self.tasks if not task["completed"]]
        try:
            self.save()
        except Exception:
            self.tasks = self._undo_stack.pop()
            raise
        return completed_count

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search tasks case-insensitively by ID, title, description, category, or tags."""
        return search_tasks(self.tasks, query)

    def filter(
        self,
        *,
        status: str = "all",
        priority: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        overdue_only: bool = False,
        reference_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Filter tasks by status, priority, category, tag, or overdue state."""
        return filter_tasks(
            self.tasks,
            status=status,
            priority=priority,
            category=category,
            tag=tag,
            overdue_only=overdue_only,
            reference_date=reference_date,
        )

    def sort(
        self,
        by: str = "id",
        descending: bool = False,
        tasks_subset: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Return a sorted copy of tasks."""
        source = self.tasks if tasks_subset is None else tasks_subset
        return sort_tasks(source, by=by, descending=descending)

    def get_statistics(self, reference_date: date | None = None) -> dict[str, Any]:
        """Compute summary statistics across all tasks."""
        return get_statistics(self.tasks, reference_date=reference_date)

    def export_csv(self, output_path: Path) -> Path:
        """Export all current tasks to a CSV file."""
        return export_tasks_to_csv(self.tasks, output_path)


# ---------------------------------------------------------------------------
# Pure helper functions & backward-compatible procedural API
# ---------------------------------------------------------------------------


def load_tasks(data_file: Path = DATA_FILE) -> list[dict[str, Any]]:
    """Load tasks from the JSON data file."""
    return load_tasks_data(data_file)


def save_tasks(tasks: list[dict[str, Any]], data_file: Path = DATA_FILE) -> None:
    """Save tasks atomically to the JSON data file."""
    save_tasks_data(tasks, data_file=data_file)


def add_task(
    tasks: list[dict[str, Any]],
    title: str,
    description: str = "",
    priority: str = "Medium",
    category: str = "General",
    due_date: str | None = None,
    tags: list[str] | str | None = None,
    data_file: Path = DATA_FILE,
) -> dict[str, Any] | None:
    """Add a task to an existing tasks list and persist it."""
    try:
        task_id = max((task["id"] for task in tasks), default=0) + 1
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
            tags=normalize_tags(tags),
        ).to_dict()
    except ValueError as error:
        print(error)
        return None

    tasks.append(task)
    save_tasks(tasks, data_file=data_file)
    print("Task added successfully!")
    return task


def view_tasks(tasks: list[dict[str, Any]]) -> None:
    """Print tasks in a readable terminal format."""
    if not tasks:
        print("\nNo tasks found. Add a new task first.")
        return

    print("\n===== YOUR TASKS =====")
    for task in tasks:
        status = "Completed" if task["completed"] else "Pending"
        priority = task.get("priority", "Medium")
        category = task.get("category", "General")
        due = f" | Due: {task['due_date']}" if task.get("due_date") else ""
        print(f"ID: {task['id']} | [{priority}] {task['title']} ({category}){due} | {status}")


def complete_task(
    tasks: list[dict[str, Any]],
    task_id: int,
    data_file: Path = DATA_FILE,
) -> bool:
    """Mark a task as completed in the given tasks list and save."""
    for index, record in enumerate(tasks):
        if record["id"] == task_id:
            if record["completed"]:
                print("This task is already completed.")
                return False
            task = Task.from_dict(record)
            task.mark_completed()
            tasks[index] = task.to_dict()
            save_tasks(tasks, data_file=data_file)
            print("Task marked as completed!")
            return True

    print("Task ID not found!")
    return False


def reopen_task(
    tasks: list[dict[str, Any]],
    task_id: int,
    data_file: Path = DATA_FILE,
) -> bool:
    """Reopen a completed task in the given tasks list and save."""
    for index, record in enumerate(tasks):
        if record["id"] == task_id:
            if not record["completed"]:
                print("This task is already pending.")
                return False
            task = Task.from_dict(record)
            task.reopen()
            tasks[index] = task.to_dict()
            save_tasks(tasks, data_file=data_file)
            print("Task reopened!")
            return True

    print("Task ID not found!")
    return False


def delete_task(
    tasks: list[dict[str, Any]],
    task_id: int,
    data_file: Path = DATA_FILE,
) -> bool:
    """Delete a task by ID from the given tasks list and save."""
    for index, record in enumerate(tasks):
        if record["id"] == task_id:
            tasks.pop(index)
            save_tasks(tasks, data_file=data_file)
            print("Task deleted successfully!")
            return True

    print("Task ID not found!")
    return False


def search_tasks(tasks: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Return tasks matching the query across ID, title, description, category, or tags."""
    cleaned = query.strip().lower()
    if not cleaned:
        return list(tasks)

    matches: list[dict[str, Any]] = []
    for task in tasks:
        haystacks = [
            str(task.get("id", "")),
            str(task.get("title", "")).lower(),
            str(task.get("description", "")).lower(),
            str(task.get("category", "")).lower(),
            " ".join(str(tag).lower() for tag in task.get("tags", [])),
        ]
        if any(cleaned in field for field in haystacks):
            matches.append(task)
    return matches


def filter_tasks(
    tasks: list[dict[str, Any]],
    *,
    status: str = "all",
    priority: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    overdue_only: bool = False,
    reference_date: date | None = None,
) -> list[dict[str, Any]]:
    """Return tasks matching all provided filter criteria."""
    status_norm = status.strip().lower()
    if status_norm not in {"all", "pending", "completed"}:
        raise ValueError("Status filter must be 'all', 'pending', or 'completed'.")

    priority_norm = normalize_priority(priority) if priority and priority.strip() else None
    category_norm = category.strip().lower() if category and category.strip() else None
    tag_norm = tag.strip().lower() if tag and tag.strip() else None

    result: list[dict[str, Any]] = []
    for record in tasks:
        if status_norm == "pending" and record["completed"]:
            continue
        if status_norm == "completed" and not record["completed"]:
            continue
        if priority_norm and record.get("priority", "Medium") != priority_norm:
            continue
        if category_norm and record.get("category", "General").lower() != category_norm:
            continue
        if tag_norm and not any(t.lower() == tag_norm for t in record.get("tags", [])):
            continue
        if overdue_only:
            if not Task.from_dict(record).is_overdue(reference_date=reference_date):
                continue
        result.append(record)
    return result


def sort_tasks(
    tasks: list[dict[str, Any]],
    *,
    by: str = "id",
    descending: bool = False,
) -> list[dict[str, Any]]:
    """Return a sorted copy of tasks by the specified key."""
    key_name = by.strip().lower()
    valid_keys = {"id", "title", "priority", "due_date", "created_at", "status"}
    if key_name not in valid_keys:
        raise ValueError(f"Invalid sort key '{by}'. Choose from: {', '.join(sorted(valid_keys))}.")

    if key_name == "due_date":
        def due_key(item: dict[str, Any]) -> tuple[int, str, int]:
            due = item.get("due_date")
            if due:
                return (0, due, item["id"])
            return (1, "9999-12-31", item["id"])

        ordered = sorted(tasks, key=due_key)
        if descending:
            with_due = [item for item in ordered if item.get("due_date")][::-1]
            without_due = [item for item in ordered if not item.get("due_date")]
            return with_due + without_due
        return ordered

    key_extractors = {
        "id": lambda item: item["id"],
        "title": lambda item: (item["title"].lower(), item["id"]),
        "priority": lambda item: (PRIORITY_WEIGHTS.get(item.get("priority", "Medium"), 2), -item["id"]),
        "created_at": lambda item: (item.get("created_at", ""), item["id"]),
        "status": lambda item: (1 if item["completed"] else 0, item["id"]),
    }

    return sorted(tasks, key=key_extractors[key_name], reverse=descending)


def get_statistics(
    tasks: list[dict[str, Any]],
    reference_date: date | None = None,
) -> dict[str, Any]:
    """Compute task counts, completion rate, overdue tasks, and breakdowns."""
    total = len(tasks)
    completed = sum(1 for item in tasks if item["completed"])
    pending = total - completed
    completion_rate = (completed / total * 100.0) if total else 0.0

    overdue_tasks: list[dict[str, Any]] = []
    due_today = 0
    today = reference_date or date.today()

    by_priority: dict[str, dict[str, int]] = {
        level: {"total": 0, "pending": 0, "completed": 0}
        for level in VALID_PRIORITIES
    }
    by_category: dict[str, dict[str, int]] = {}

    for record in tasks:
        task_obj = Task.from_dict(record)
        priority = task_obj.priority
        category = task_obj.category

        by_priority[priority]["total"] += 1
        if task_obj.completed:
            by_priority[priority]["completed"] += 1
        else:
            by_priority[priority]["pending"] += 1

        cat_stats = by_category.setdefault(category, {"total": 0, "pending": 0, "completed": 0})
        cat_stats["total"] += 1
        if task_obj.completed:
            cat_stats["completed"] += 1
        else:
            cat_stats["pending"] += 1

        if task_obj.is_overdue(reference_date=today):
            overdue_tasks.append(record)
        elif not task_obj.completed and task_obj.days_remaining(reference_date=today) == 0:
            due_today += 1

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "completion_rate": round(completion_rate, 1),
        "overdue_count": len(overdue_tasks),
        "overdue_tasks": overdue_tasks,
        "due_today_count": due_today,
        "by_priority": by_priority,
        "by_category": dict(sorted(by_category.items(), key=lambda kv: (-kv[1]["total"], kv[0].lower()))),
    }


def search_tasks(tasks: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Return tasks matching the query across ID, title, description, category, or tags."""
    cleaned = query.strip().lower()
    if not cleaned:
        return list(tasks)

    matches: list[dict[str, Any]] = []
    for task in tasks:
        haystacks = [
            str(task.get("id", "")),
            str(task.get("title", "")).lower(),
            str(task.get("description", "")).lower(),
            str(task.get("category", "")).lower(),
            " ".join(str(tag).lower() for tag in task.get("tags", [])),
        ]
        if any(cleaned in field for field in haystacks):
            matches.append(task)
    return matches


def filter_tasks(
    tasks: list[dict[str, Any]],
    *,
    status: str = "all",
    priority: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    overdue_only: bool = False,
    reference_date: date | None = None,
) -> list[dict[str, Any]]:
    """Return tasks matching all provided filter criteria."""
    status_norm = status.strip().lower()
    if status_norm not in {"all", "pending", "completed"}:
        raise ValueError("Status filter must be 'all', 'pending', or 'completed'.")

    priority_norm = normalize_priority(priority) if priority and priority.strip() else None
    category_norm = category.strip().lower() if category and category.strip() else None
    tag_norm = tag.strip().lower() if tag and tag.strip() else None

    result: list[dict[str, Any]] = []
    for record in tasks:
        if status_norm == "pending" and record["completed"]:
            continue
        if status_norm == "completed" and not record["completed"]:
            continue
        if priority_norm and record.get("priority", "Medium") != priority_norm:
            continue
        if category_norm and record.get("category", "General").lower() != category_norm:
            continue
        if tag_norm and not any(t.lower() == tag_norm for t in record.get("tags", [])):
            continue
        if overdue_only:
            if not Task.from_dict(record).is_overdue(reference_date=reference_date):
                continue
        result.append(record)
    return result


def sort_tasks(
    tasks: list[dict[str, Any]],
    *,
    by: str = "id",
    descending: bool = False,
) -> list[dict[str, Any]]:
    """Return a sorted copy of tasks by the specified key."""
    key_name = by.strip().lower()
    valid_keys = {"id", "title", "priority", "due_date", "created_at", "status"}
    if key_name not in valid_keys:
        raise ValueError(f"Invalid sort key '{by}'. Choose from: {', '.join(sorted(valid_keys))}.")

    if key_name == "due_date":
        def due_key(item: dict[str, Any]) -> tuple[int, str, int]:
            due = item.get("due_date")
            if due:
                return (0, due, item["id"])
            return (1, "9999-12-31", item["id"])

        ordered = sorted(tasks, key=due_key)
        if descending:
            with_due = [item for item in ordered if item.get("due_date")][::-1]
            without_due = [item for item in ordered if not item.get("due_date")]
            return with_due + without_due
        return ordered

    key_extractors = {
        "id": lambda item: item["id"],
        "title": lambda item: (item["title"].lower(), item["id"]),
        "priority": lambda item: (PRIORITY_WEIGHTS.get(item.get("priority", "Medium"), 2), -item["id"]),
        "created_at": lambda item: (item.get("created_at", ""), item["id"]),
        "status": lambda item: (1 if item["completed"] else 0, item["id"]),
    }

    return sorted(tasks, key=key_extractors[key_name], reverse=descending)


def get_statistics(
    tasks: list[dict[str, Any]],
    reference_date: date | None = None,
) -> dict[str, Any]:
    """Compute task counts, completion rate, overdue tasks, and breakdowns."""
    total = len(tasks)
    completed = sum(1 for item in tasks if item["completed"])
    pending = total - completed
    completion_rate = (completed / total * 100.0) if total else 0.0

    overdue_tasks: list[dict[str, Any]] = []
    due_today = 0
    today = reference_date or date.today()

    by_priority: dict[str, dict[str, int]] = {
        level: {"total": 0, "pending": 0, "completed": 0}
        for level in VALID_PRIORITIES
    }
    by_category: dict[str, dict[str, int]] = {}

    for record in tasks:
        task_obj = Task.from_dict(record)
        priority = task_obj.priority
        category = task_obj.category

        by_priority[priority]["total"] += 1
        if task_obj.completed:
            by_priority[priority]["completed"] += 1
        else:
            by_priority[priority]["pending"] += 1

        cat_stats = by_category.setdefault(category, {"total": 0, "pending": 0, "completed": 0})
        cat_stats["total"] += 1
        if task_obj.completed:
            cat_stats["completed"] += 1
        else:
            cat_stats["pending"] += 1

        if task_obj.is_overdue(reference_date=today):
            overdue_tasks.append(record)
        elif not task_obj.completed and task_obj.days_remaining(reference_date=today) == 0:
            due_today += 1

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "completion_rate": round(completion_rate, 1),
        "overdue_count": len(overdue_tasks),
        "overdue_tasks": overdue_tasks,
        "due_today_count": due_today,
        "by_priority": by_priority,
        "by_category": dict(sorted(by_category.items(), key=lambda kv: (-kv[1]["total"], kv[0].lower()))),
    }

