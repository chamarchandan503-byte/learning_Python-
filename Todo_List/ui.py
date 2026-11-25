"""Terminal presentation, formatted tables, dashboard, and input prompt helpers."""

from __future__ import annotations

import os
import sys
from typing import Any

from models import VALID_PRIORITIES, Task


def configure_console() -> None:
    """Enable UTF-8 output and Windows ANSI escape processing when available."""
    if os.name == "nt":
        os.system("")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


class Style:
    """ANSI color helper with automatic fallback when color is disabled."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    @classmethod
    def enabled(cls) -> bool:
        return not os.environ.get("NO_COLOR") and sys.stdout.isatty()

    @classmethod
    def paint(cls, text: str, *codes: str) -> str:
        if not cls.enabled() or not codes:
            return text
        return f"{''.join(codes)}{text}{cls.RESET}"


def print_success(message: str) -> None:
    print(Style.paint(f"✔ {message}", Style.GREEN, Style.BOLD))


def print_error(message: str) -> None:
    print(Style.paint(f"✘ {message}", Style.RED, Style.BOLD))


def print_warning(message: str) -> None:
    print(Style.paint(f"⚠ {message}", Style.YELLOW, Style.BOLD))


def print_info(message: str) -> None:
    print(Style.paint(f"ℹ {message}", Style.CYAN))


def truncate_text(text: str, max_len: int) -> str:
    """Truncate text cleanly with ellipsis when exceeding max_len."""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def _priority_badge(priority: str) -> str:
    colors = {
        "Urgent": Style.RED,
        "High": Style.YELLOW,
        "Medium": Style.CYAN,
        "Low": Style.GRAY,
    }
    padded = f"{priority:<6}"
    return Style.paint(padded, colors.get(priority, Style.WHITE), Style.BOLD)


def _status_badge(task: dict[str, Any]) -> str:
    task_obj = Task.from_dict(task)
    if task_obj.completed:
        return Style.paint("✓ Done   ", Style.GREEN, Style.BOLD)
    if task_obj.is_overdue():
        return Style.paint("! Overdue", Style.RED, Style.BOLD)
    return Style.paint("○ Pending", Style.YELLOW)


def _progress_bar(percentage: float, width: int = 24) -> str:
    filled = int(round((percentage / 100.0) * width))
    filled = max(0, min(width, filled))
    bar = "█" * filled + "░" * (width - filled)
    color = Style.GREEN if percentage >= 75 else (Style.CYAN if percentage >= 40 else Style.YELLOW)
    return Style.paint(f"[{bar}]", color)


def print_banner(stats: dict[str, Any]) -> None:
    """Display the application header and a compact live summary."""
    print()
    title_line = "══════════════ TO-DO LIST MANAGER ══════════════"
    print(Style.paint(title_line, Style.CYAN, Style.BOLD))

    bar = _progress_bar(stats["completion_rate"], width=18)
    summary = (
        f"Total: {stats['total']} | "
        f"Pending: {stats['pending']} | "
        f"Completed: {stats['completed']} | "
        f"Overdue: {stats['overdue_count']} | "
        f"{bar} {stats['completion_rate']:.1f}%"
    )
    print(summary)
    print(Style.paint("─" * 58, Style.GRAY))


def print_menu(can_undo: bool = False) -> None:
    """Display the interactive CLI menu."""
    undo_hint = Style.paint(" (available)", Style.GREEN) if can_undo else Style.paint(" (empty)", Style.GRAY)
    print(Style.paint("\nMENU OPTIONS:", Style.BOLD))
    print("  1. Add New Task")
    print("  2. View All Tasks")
    print("  3. View Task Details")
    print("  4. Search Tasks")
    print("  5. Filter & Sort Tasks")
    print("  6. Edit / Update Task")
    print("  7. Mark Task Completed / Reopen")
    print("  8. Delete Task")
    print("  9. Clear Completed Tasks")
    print(" 10. Productivity Dashboard")
    print(" 11. Export Tasks to CSV")
    print(f" 12. Undo Last Change{undo_hint}")
    print(" 13. Restore from Backup")
    print("  0. Exit")


def render_tasks_table(tasks: list[dict[str, Any]], heading: str = "YOUR TASKS") -> None:
    """Render a list of task dictionaries as an aligned Unicode table."""
    print(f"\n{Style.paint(f'===== {heading} ({len(tasks)}) =====', Style.CYAN, Style.BOLD)}")
    if not tasks:
        print_info("No matching tasks found.")
        return

    header = (
        f"{'ID':>4} │ {'Status':<9} │ {'Pri':<6} │ "
        f"{'Title':<28} │ {'Category':<12} │ {'Due Date':<10} │ {'Tags'}"
    )
    divider = "─" * 92
    print(Style.paint(divider, Style.GRAY))
    print(Style.paint(header, Style.BOLD))
    print(Style.paint(divider, Style.GRAY))

    for task in tasks:
        task_id = f"{task['id']:>4}"
        status = _status_badge(task)
        priority = _priority_badge(task.get("priority", "Medium"))
        title = truncate_text(task["title"], 28).ljust(28)
        if task["completed"]:
            title = Style.paint(title, Style.DIM)

        category = truncate_text(task.get("category", "General"), 12).ljust(12)
        due = (task.get("due_date") or "—").ljust(10)
        tags_str = ", ".join(task.get("tags", [])) or "—"
        tags_str = truncate_text(tags_str, 18)

        print(f"{task_id} │ {status} │ {priority} │ {title} │ {category} │ {due} │ {tags_str}")

    print(Style.paint(divider, Style.GRAY))


def render_task_detail(task: dict[str, Any]) -> None:
    """Render full details of a single task."""
    task_obj = Task.from_dict(task)
    print(f"\n{Style.paint(f'===== TASK #{task_obj.id} DETAILS =====', Style.CYAN, Style.BOLD)}")
    print(f"Title       : {Style.paint(task_obj.title, Style.BOLD)}")
    print(f"Status      : {_status_badge(task)}")
    print(f"Priority    : {_priority_badge(task_obj.priority)}")
    print(f"Category    : {task_obj.category}")

    if task_obj.due_date:
        remaining = task_obj.days_remaining()
        if task_obj.completed:
            due_note = task_obj.due_date
        elif remaining is not None and remaining < 0:
            due_note = Style.paint(f"{task_obj.due_date} ({abs(remaining)} day(s) overdue)", Style.RED)
        elif remaining == 0:
            due_note = Style.paint(f"{task_obj.due_date} (Due today)", Style.YELLOW)
        else:
            due_note = f"{task_obj.due_date} ({remaining} day(s) left)"
    else:
        due_note = "None"

    print(f"Due Date    : {due_note}")
    print(f"Tags        : {', '.join(task_obj.tags) if task_obj.tags else 'None'}")
    print(f"Description : {task_obj.description if task_obj.description else 'None'}")
    print(f"Created At  : {task_obj.created_at}")
    print(f"Updated At  : {task_obj.updated_at}")
    if task_obj.completed_at:
        print(f"Completed At: {task_obj.completed_at}")


def render_dashboard(stats: dict[str, Any]) -> None:
    """Render productivity analytics and category/priority breakdowns."""
    print(f"\n{Style.paint('===== PRODUCTIVITY DASHBOARD =====', Style.MAGENTA, Style.BOLD)}")
    bar = _progress_bar(stats["completion_rate"], width=28)
    print(f"Completion Progress : {bar} {stats['completion_rate']:.1f}%")
    print(
        f"Summary             : {stats['total']} total | "
        f"{stats['completed']} completed | "
        f"{stats['pending']} pending | "
        f"{stats['due_today_count']} due today | "
        f"{stats['overdue_count']} overdue"
    )

    print(Style.paint("\nBy Priority:", Style.BOLD))
    for level in VALID_PRIORITIES:
        data = stats["by_priority"][level]
        print(
            f"  {_priority_badge(level)} -> Total: {data['total']:<3} "
            f"(Pending: {data['pending']}, Completed: {data['completed']})"
        )

    print(Style.paint("\nBy Category:", Style.BOLD))
    if not stats["by_category"]:
        print("  No categories yet.")
    else:
        for category, data in stats["by_category"].items():
            print(
                f"  {truncate_text(category, 16):<16} -> Total: {data['total']:<3} "
                f"(Pending: {data['pending']}, Completed: {data['completed']})"
            )

    if stats["overdue_tasks"]:
        print(Style.paint("\nOverdue Tasks:", Style.RED, Style.BOLD))
        for item in stats["overdue_tasks"]:
            print(f"  • #{item['id']} [{item['priority']}] {item['title']} (Due: {item['due_date']})")
