"""Data models and validation helpers for the To-Do List application."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

VALID_PRIORITIES: tuple[str, ...] = ("Low", "Medium", "High", "Urgent")
PRIORITY_WEIGHTS: dict[str, int] = {
    "Urgent": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}
DATE_FORMAT = "%Y-%m-%d"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_timestamp() -> str:
    """Return the current local timestamp formatted consistently."""
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def normalize_priority(value: str | None) -> str:
    """Validate and normalize a priority string to title case."""
    if value is None or not str(value).strip():
        return "Medium"

    cleaned = str(value).strip().lower()
    mapping = {
        "l": "Low",
        "low": "Low",
        "m": "Medium",
        "med": "Medium",
        "medium": "Medium",
        "h": "High",
        "high": "High",
        "u": "Urgent",
        "urgent": "Urgent",
    }
    if cleaned not in mapping:
        raise ValueError(
            f"Invalid priority '{value}'. Choose from: {', '.join(VALID_PRIORITIES)}."
        )
    return mapping[cleaned]


def validate_due_date(value: str | None) -> str | None:
    """Validate an optional YYYY-MM-DD due date string."""
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    try:
        parsed = datetime.strptime(cleaned, DATE_FORMAT)
    except ValueError as exc:
        raise ValueError(
            f"Invalid due date '{value}'. Expected format YYYY-MM-DD (e.g. 2026-12-31)."
        ) from exc

    return parsed.strftime(DATE_FORMAT)


def normalize_tags(tags: list[str] | str | None) -> list[str]:
    """Normalize a list or comma-separated string of tags without duplicates."""
    if tags is None:
        return []

    raw_items = tags.split(",") if isinstance(tags, str) else tags
    if not isinstance(raw_items, (list, tuple)):
        raise ValueError("Tags must be a list of strings or a comma-separated string.")

    result: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        tag = str(item).strip()
        if not tag:
            continue
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            result.append(tag)
    return result


@dataclass
class Task:
    """Represents a single To-Do task record."""

    id: int
    title: str
    completed: bool = False
    description: str = ""
    priority: str = "Medium"
    category: str = "General"
    due_date: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_timestamp)
    updated_at: str = field(default_factory=now_timestamp)
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id <= 0:
            raise ValueError("Task ID must be a positive integer.")

        self.title = str(self.title).strip()
        if not self.title:
            raise ValueError("Task title cannot be empty.")

        if not isinstance(self.completed, bool):
            raise ValueError("Task 'completed' field must be a boolean.")

        self.description = str(self.description or "").strip()
        self.priority = normalize_priority(self.priority)

        category = str(self.category or "").strip()
        self.category = category if category else "General"

        self.due_date = validate_due_date(self.due_date)
        self.tags = normalize_tags(self.tags)

        self.created_at = str(self.created_at or now_timestamp()).strip() or now_timestamp()
        self.updated_at = str(self.updated_at or self.created_at).strip() or self.created_at

        if self.completed and not self.completed_at:
            self.completed_at = self.updated_at
        elif not self.completed:
            self.completed_at = None

    def is_overdue(self, reference_date: date | None = None) -> bool:
        """Return True if the task is incomplete and past its due date."""
        if self.completed or not self.due_date:
            return False
        today = reference_date or date.today()
        due = datetime.strptime(self.due_date, DATE_FORMAT).date()
        return due < today

    def days_remaining(self, reference_date: date | None = None) -> int | None:
        """Return signed days until due date (negative if overdue), or None."""
        if not self.due_date:
            return None
        today = reference_date or date.today()
        due = datetime.strptime(self.due_date, DATE_FORMAT).date()
        return (due - today).days

    def mark_completed(self) -> None:
        """Mark the task as completed and update timestamps."""
        timestamp = now_timestamp()
        self.completed = True
        self.completed_at = timestamp
        self.updated_at = timestamp

    def reopen(self) -> None:
        """Mark a completed task as pending again."""
        self.completed = False
        self.completed_at = None
        self.updated_at = now_timestamp()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the task into a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "due_date": self.due_date,
            "tags": list(self.tags),
            "completed": self.completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Build a Task from a dictionary, supporting legacy minimal records."""
        if not isinstance(data, dict):
            raise ValueError("Invalid task record: expected a JSON object.")

        required = {"id", "title", "completed"}
        if not required.issubset(data):
            missing = ", ".join(sorted(required - set(data)))
            raise ValueError(f"Task record is missing required field(s): {missing}.")

        return cls(
            id=data["id"],
            title=data["title"],
            completed=data["completed"],
            description=data.get("description", ""),
            priority=data.get("priority", "Medium"),
            category=data.get("category", "General"),
            due_date=data.get("due_date"),
            tags=data.get("tags", []),
            created_at=data.get("created_at") or now_timestamp(),
            updated_at=data.get("updated_at") or data.get("created_at") or now_timestamp(),
            completed_at=data.get("completed_at"),
        )
