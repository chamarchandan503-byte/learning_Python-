"""Persistent JSON storage, atomic writes, backup recovery, and CSV export."""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from models import Task

DEFAULT_DATA_FILE = Path(__file__).with_name("tasks.json")
CSV_HEADERS = (
    "id",
    "title",
    "description",
    "priority",
    "category",
    "due_date",
    "tags",
    "completed",
    "created_at",
    "updated_at",
    "completed_at",
)


def get_backup_path(data_file: Path = DEFAULT_DATA_FILE) -> Path:
    """Return the backup file path paired with the given JSON data file."""
    return data_file.with_suffix(".backup.json")


def _validate_and_normalize_records(raw_data: Any) -> list[dict[str, Any]]:
    """Validate raw parsed JSON data and normalize each task record."""
    if not isinstance(raw_data, list):
        raise ValueError("Tasks data must be a JSON list.")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for record in raw_data:
        task = Task.from_dict(record)
        if task.id in seen_ids:
            raise ValueError(f"Duplicate task ID found: {task.id}.")
        seen_ids.add(task.id)
        normalized.append(task.to_dict())

    return normalized


def load_tasks_data(data_file: Path = DEFAULT_DATA_FILE) -> list[dict[str, Any]]:
    """Load and validate tasks from the JSON storage file."""
    path = Path(data_file)
    if not path.exists():
        return []

    try:
        raw_text = path.read_text(encoding="utf-8")
        if not raw_text.strip():
            return []
        raw_data = json.loads(raw_text)
        return _validate_and_normalize_records(raw_data)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"Cannot read {path.name}: {error}") from error


def save_tasks_data(
    tasks: list[dict[str, Any]],
    data_file: Path = DEFAULT_DATA_FILE,
    create_backup: bool = True,
) -> None:
    """Atomically save tasks to JSON, optionally keeping a backup of the prior file."""
    path = Path(data_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    normalized = _validate_and_normalize_records(tasks)

    if create_backup and path.exists():
        backup_path = get_backup_path(path)
        shutil.copy2(path, backup_path)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(normalized, temp_file, indent=4, ensure_ascii=False)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, path)
    except OSError as error:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to save {path.name}: {error}") from error


def restore_from_backup(data_file: Path = DEFAULT_DATA_FILE) -> list[dict[str, Any]]:
    """Restore tasks from the backup JSON file and persist them to data_file."""
    path = Path(data_file)
    backup_path = get_backup_path(path)
    if not backup_path.exists():
        raise FileNotFoundError(f"No backup file found at '{backup_path.name}'.")

    restored = load_tasks_data(backup_path)
    save_tasks_data(restored, data_file=path, create_backup=False)
    return restored


def export_tasks_to_csv(tasks: list[dict[str, Any]], output_path: Path) -> Path:
    """Export the given tasks list to a UTF-8 CSV file."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    normalized = _validate_and_normalize_records(tasks)

    with destination.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for task in normalized:
            row = dict(task)
            row["tags"] = ", ".join(task.get("tags", []))
            row["due_date"] = task.get("due_date") or ""
            row["completed_at"] = task.get("completed_at") or ""
            writer.writerow(row)

    return destination
