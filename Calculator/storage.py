"""Atomic JSON persistence, automatic backup recovery, and CSV export for calculator history."""

from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_MAX_HISTORY = 200


@dataclass(frozen=True)
class HistoryEntry:
    """Single persisted calculation record."""

    id: int
    timestamp: str
    category: str
    expression: str
    result: str
    numeric_value: float | None = None
    angle_mode: str = "DEG"

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback_id: int) -> HistoryEntry:
        """Create a validated HistoryEntry from raw JSON dictionary data."""
        raw_num = data.get("numeric_value")
        numeric_value = float(raw_num) if isinstance(raw_num, (int, float)) and not isinstance(raw_num, bool) else None
        return cls(
            id=int(data.get("id", fallback_id)),
            timestamp=str(data.get("timestamp") or ""),
            category=str(data.get("category") or "Expression"),
            expression=str(data.get("expression") or ""),
            result=str(data.get("result") or ""),
            numeric_value=numeric_value,
            angle_mode=str(data.get("angle_mode") or "DEG"),
        )


class HistoryStore:
    """Manages calculation history and calculator state with atomic JSON saves."""

    def __init__(self, data_path: str | Path | None = None, max_entries: int = DEFAULT_MAX_HISTORY) -> None:
        base_dir = Path(__file__).resolve().parent
        self.data_path = Path(data_path) if data_path else base_dir / "calculator_data.json"
        self.backup_path = self.data_path.with_suffix(".backup.json")
        self.max_entries = max(1, max_entries)

        self.entries: list[HistoryEntry] = []
        self.state: dict[str, Any] = {
            "angle_mode": "DEG",
            "memory": 0.0,
            "last_answer": 0.0,
            "precision": 12,
        }
        self._next_id = 1
        self.recovered_from_backup = False
        self.load()

    def _parse_file(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            raise ValueError("storage payload must be a JSON object")
        return payload

    def _apply_payload(self, payload: dict[str, Any]) -> None:
        raw_state = payload.get("state")
        if isinstance(raw_state, dict):
            angle_mode = str(raw_state.get("angle_mode", "DEG")).upper()
            self.state["angle_mode"] = angle_mode if angle_mode in ("DEG", "RAD") else "DEG"

            for key, default in (("memory", 0.0), ("last_answer", 0.0)):
                val = raw_state.get(key, default)
                self.state[key] = float(val) if isinstance(val, (int, float)) and not isinstance(val, bool) else default

            prec = raw_state.get("precision", 12)
            if isinstance(prec, int) and not isinstance(prec, bool) and 4 <= prec <= 15:
                self.state["precision"] = prec

        raw_entries = payload.get("entries", [])
        loaded: list[HistoryEntry] = []
        max_id = 0
        if isinstance(raw_entries, list):
            for idx, item in enumerate(raw_entries, start=1):
                if isinstance(item, dict):
                    entry = HistoryEntry.from_dict(item, idx)
                    loaded.append(entry)
                    if entry.id > max_id:
                        max_id = entry.id

        self.entries = loaded[-self.max_entries :]
        self._next_id = max_id + 1

    def load(self) -> None:
        """Load history and state from primary JSON, falling back to backup if corrupt."""
        self.recovered_from_backup = False
        if self.data_path.exists():
            try:
                payload = self._parse_file(self.data_path)
                self._apply_payload(payload)
                return
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                if self.backup_path.exists():
                    try:
                        payload = self._parse_file(self.backup_path)
                        self._apply_payload(payload)
                        self.recovered_from_backup = True
                        self.save()
                        return
                    except (OSError, ValueError, TypeError, json.JSONDecodeError):
                        pass
        elif self.backup_path.exists():
            try:
                payload = self._parse_file(self.backup_path)
                self._apply_payload(payload)
                self.recovered_from_backup = True
                return
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass

        self.entries = []
        self._next_id = 1

    def _atomic_write_text(self, target: Path, content: str) -> None:
        """Atomically write text via temp file with brief retries for Windows file locks."""
        tmp_path = target.with_name(f"{target.stem}.{os.getpid()}.tmp")
        tmp_path.write_text(content, encoding="utf-8")
        try:
            for attempt in range(5):
                try:
                    os.replace(tmp_path, target)
                    return
                except PermissionError:
                    if attempt == 4:
                        break
                    time.sleep(0.02 * (attempt + 1))
            # Fallback if another Windows process (e.g., AV/indexer) holds replace lock
            target.write_text(content, encoding="utf-8")
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def save(self) -> None:
        """Atomically persist state and history to primary JSON and mirror to backup."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state": self.state,
            "entries": [asdict(entry) for entry in self.entries[-self.max_entries :]],
        }
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)

        self._atomic_write_text(self.data_path, serialized)
        try:
            self._atomic_write_text(self.backup_path, serialized)
        except OSError:
            pass

    def update_state(
        self,
        *,
        angle_mode: str | None = None,
        memory: float | None = None,
        last_answer: float | None = None,
        precision: int | None = None,
    ) -> None:
        """Update and persist calculator state."""
        if angle_mode is not None:
            self.state["angle_mode"] = angle_mode
        if memory is not None:
            self.state["memory"] = float(memory)
        if last_answer is not None:
            self.state["last_answer"] = float(last_answer)
        if precision is not None:
            self.state["precision"] = int(precision)
        self.save()

    def add_entry(
        self,
        *,
        category: str,
        expression: str,
        result: str,
        numeric_value: float | None = None,
        angle_mode: str = "DEG",
    ) -> HistoryEntry:
        """Record a new calculation in history and persist immediately."""
        entry = HistoryEntry(
            id=self._next_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            category=category,
            expression=expression,
            result=result,
            numeric_value=numeric_value,
            angle_mode=angle_mode,
        )
        self._next_id += 1
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]
        self.save()
        return entry

    def get_by_id(self, entry_id: int) -> HistoryEntry | None:
        """Return a history entry by ID, or None if not found."""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def search(self, query: str) -> list[HistoryEntry]:
        """Search entries case-insensitively across category, expression, and result."""
        q = query.strip().lower()
        if not q:
            return list(self.entries)
        return [
            entry
            for entry in self.entries
            if q in entry.category.lower() or q in entry.expression.lower() or q in entry.result.lower()
        ]

    def clear(self) -> int:
        """Clear all history entries and return count removed."""
        count = len(self.entries)
        self.entries = []
        self.save()
        return count

    def export_csv(self, output_path: str | Path | None = None) -> Path:
        """Export calculation history to a UTF-8 BOM CSV file."""
        target = Path(output_path) if output_path else self.data_path.parent / "calculator_history.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["ID", "Timestamp", "Category", "Expression", "Result", "Angle Mode"])
            for entry in self.entries:
                writer.writerow(
                    [entry.id, entry.timestamp, entry.category, entry.expression, entry.result, entry.angle_mode]
                )
        return target
