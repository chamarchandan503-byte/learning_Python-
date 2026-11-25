"""Interactive CLI entry point for the To-Do List Manager."""

from __future__ import annotations

from pathlib import Path

from models import VALID_PRIORITIES, normalize_priority, validate_due_date
from storage import DEFAULT_DATA_FILE, get_backup_path
from todo import TodoManager
from ui import (
    configure_console,
    print_banner,
    print_error,
    print_info,
    print_menu,
    print_success,
    print_warning,
    render_dashboard,
    render_task_detail,
    render_tasks_table,
)


def prompt_int(prompt: str) -> int | None:
    """Prompt for a positive integer ID, returning None if cancelled or invalid."""
    raw = input(prompt).strip()
    if not raw:
        print_info("Operation cancelled.")
        return None
    try:
        value = int(raw)
    except ValueError:
        print_error("Please enter a valid numeric Task ID.")
        return None
    if value <= 0:
        print_error("Task ID must be a positive number.")
        return None
    return value


def prompt_priority(default: str = "Medium", allow_keep: bool = False) -> str | None:
    """Prompt for task priority until valid. Returns None only when keeping existing."""
    hint = f"Low/Medium/High/Urgent"
    prompt_text = (
        f"Enter priority ({hint}) [Enter to keep '{default}']: "
        if allow_keep
        else f"Enter priority ({hint}) [default: {default}]: "
    )
    while True:
        raw = input(prompt_text).strip()
        if not raw:
            return None if allow_keep else default
        try:
            return normalize_priority(raw)
        except ValueError as error:
            print_error(str(error))


def prompt_due_date(current: str | None = None, allow_keep: bool = False) -> str | None | object:
    """Prompt for YYYY-MM-DD due date; returns sentinel ... when keeping existing."""
    if allow_keep:
        shown = current or "None"
        prompt_text = (
            f"Enter due date YYYY-MM-DD (type '-' to clear, Enter to keep '{shown}'): "
        )
    else:
        prompt_text = "Enter due date YYYY-MM-DD (optional, Enter to skip): "

    while True:
        raw = input(prompt_text).strip()
        if not raw:
            return ... if allow_keep else None
        if allow_keep and raw == "-":
            return None
        try:
            return validate_due_date(raw)
        except ValueError as error:
            print_error(str(error))


def prompt_confirm(prompt: str) -> bool:
    """Ask for yes/no confirmation."""
    answer = input(f"{prompt} (y/N): ").strip().lower()
    return answer in {"y", "yes"}


def handle_add_task(manager: TodoManager) -> None:
    title = input("Enter task title: ").strip()
    if not title:
        print_error("Task title cannot be empty!")
        return

    description = input("Enter description (optional): ").strip()
    priority = prompt_priority("Medium", allow_keep=False) or "Medium"
    category = input("Enter category [default: General]: ").strip() or "General"
    due_date = prompt_due_date(allow_keep=False)
    tags = input("Enter comma-separated tags (optional): ").strip()

    try:
        task = manager.add_task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=None if due_date is ... else due_date,  # type: ignore[arg-type]
            tags=tags,
        )
    except ValueError as error:
        print_error(str(error))
        return

    print_success(f"Task #{task['id']} '{task['title']}' added successfully!")


def handle_view_details(manager: TodoManager) -> None:
    task_id = prompt_int("Enter Task ID to view details: ")
    if task_id is None:
        return
    task = manager.get_task(task_id)
    if not task:
        print_error(f"Task ID {task_id} not found!")
        return
    render_task_detail(task)


def handle_search(manager: TodoManager) -> None:
    query = input("Enter search keyword (ID, title, description, category, or tag): ").strip()
    if not query:
        print_info("Empty search query. Showing all tasks.")
        render_tasks_table(manager.tasks, heading="ALL TASKS")
        return
    results = manager.search(query)
    render_tasks_table(results, heading=f"SEARCH RESULTS FOR '{query}'")


def handle_filter_and_sort(manager: TodoManager) -> None:
    print_info("Leave any filter blank to include all.")
    status = input("Status (all / pending / completed) [all]: ").strip() or "all"
    priority = input(f"Priority ({'/'.join(VALID_PRIORITIES)}) [any]: ").strip() or None
    category = input("Category [any]: ").strip() or None
    tag = input("Tag [any]: ").strip() or None
    overdue_only = prompt_confirm("Show overdue tasks only?")

    sort_by = input("Sort by (id / priority / due_date / title / created_at / status) [id]: ").strip() or "id"
    descending = prompt_confirm("Sort descending?")

    try:
        filtered = manager.filter(
            status=status,
            priority=priority,
            category=category,
            tag=tag,
            overdue_only=overdue_only,
        )
        ordered = manager.sort(by=sort_by, descending=descending, tasks_subset=filtered)
    except ValueError as error:
        print_error(str(error))
        return

    render_tasks_table(ordered, heading="FILTERED & SORTED TASKS")


def handle_edit_task(manager: TodoManager) -> None:
    task_id = prompt_int("Enter Task ID to edit: ")
    if task_id is None:
        return

    existing = manager.get_task(task_id)
    if not existing:
        print_error(f"Task ID {task_id} not found!")
        return

    render_task_detail(existing)
    print_info("Press Enter on any field to keep its current value.")

    new_title = input(f"New title [{existing['title']}]: ").strip()
    new_desc_raw = input("New description (type '-' to clear, Enter to keep): ").strip()
    if not new_desc_raw:
        new_desc = None
    elif new_desc_raw == "-":
        new_desc = ""
    else:
        new_desc = new_desc_raw

    new_priority = prompt_priority(existing["priority"], allow_keep=True)
    new_category = input(f"New category [{existing['category']}]: ").strip() or None
    new_due = prompt_due_date(existing.get("due_date"), allow_keep=True)

    current_tags = ", ".join(existing.get("tags", [])) or "None"
    new_tags_raw = input(f"New comma-separated tags (type '-' to clear, Enter to keep '{current_tags}'): ").strip()
    if not new_tags_raw:
        new_tags = None
    elif new_tags_raw == "-":
        new_tags = []
    else:
        new_tags = new_tags_raw

    try:
        updated = manager.edit_task(
            task_id,
            title=new_title or None,
            description=new_desc,
            priority=new_priority,
            category=new_category,
            due_date=new_due,  # type: ignore[arg-type]
            tags=new_tags,
        )
    except (KeyError, ValueError) as error:
        print_error(str(error))
        return

    print_success(f"Task #{updated['id']} updated successfully!")


def handle_toggle_status(manager: TodoManager) -> None:
    task_id = prompt_int("Enter Task ID to complete/reopen: ")
    if task_id is None:
        return
    task = manager.get_task(task_id)
    if not task:
        print_error(f"Task ID {task_id} not found!")
        return

    if task["completed"]:
        if prompt_confirm(f"Task #{task_id} is already completed. Reopen it?"):
            manager.reopen_task(task_id)
            print_success(f"Task #{task_id} reopened as pending!")
    else:
        manager.complete_task(task_id)
        print_success(f"Task #{task_id} marked as completed!")


def handle_delete_task(manager: TodoManager) -> None:
    task_id = prompt_int("Enter Task ID to delete: ")
    if task_id is None:
        return
    task = manager.get_task(task_id)
    if not task:
        print_error(f"Task ID {task_id} not found!")
        return
    if prompt_confirm(f"Delete task #{task_id} '{task['title']}'?"):
        manager.delete_task(task_id)
        print_success(f"Task #{task_id} deleted successfully!")
    else:
        print_info("Deletion cancelled.")


def handle_clear_completed(manager: TodoManager) -> None:
    completed_count = sum(1 for task in manager.tasks if task["completed"])
    if completed_count == 0:
        print_info("There are no completed tasks to clear.")
        return
    if prompt_confirm(f"Remove all {completed_count} completed task(s)?"):
        removed = manager.clear_completed()
        print_success(f"Removed {removed} completed task(s).")
    else:
        print_info("Operation cancelled.")


def handle_export_csv(manager: TodoManager) -> None:
    default_csv = DEFAULT_DATA_FILE.with_name("tasks_export.csv")
    raw_path = input(f"Enter CSV path [default: {default_csv.name}]: ").strip()
    target = Path(raw_path) if raw_path else default_csv
    if not target.is_absolute():
        target = DEFAULT_DATA_FILE.parent / target

    try:
        exported = manager.export_csv(target)
    except Exception as error:
        print_error(f"Failed to export CSV: {error}")
        return
    print_success(f"Exported {len(manager.tasks)} task(s) to '{exported}'.")


def handle_restore_backup(manager: TodoManager) -> None:
    backup_path = get_backup_path(manager.data_file)
    if not backup_path.exists():
        print_warning("No backup file exists yet. Backups are created automatically on updates.")
        return
    if prompt_confirm(f"Restore tasks from '{backup_path.name}'? Current unsaved view will be replaced"):
        try:
            restored = manager.restore_backup()
        except Exception as error:
            print_error(f"Backup restore failed: {error}")
            return
        print_success(f"Restored {len(restored)} task(s) from backup!")


def initialize_manager(data_file: Path = DEFAULT_DATA_FILE) -> TodoManager:
    """Initialize TodoManager, offering backup recovery if the main file is corrupted."""
    try:
        return TodoManager(data_file=data_file, auto_load=True)
    except RuntimeError as error:
        print_error(str(error))
        backup_path = get_backup_path(data_file)
        if backup_path.exists() and prompt_confirm("A backup exists. Restore from backup?"):
            manager = TodoManager(data_file=data_file, auto_load=False)
            restored = manager.restore_backup()
            print_success(f"Recovered {len(restored)} task(s) from backup!")
            return manager
        print_error("Please fix tasks.json before continuing.")
        raise SystemExit(1) from error


def run_app(data_file: Path = DEFAULT_DATA_FILE) -> None:
    """Run the interactive To-Do List Manager CLI loop."""
    configure_console()
    manager = initialize_manager(data_file=data_file)

    try:
        while True:
            stats = manager.get_statistics()
            print_banner(stats)
            print_menu(can_undo=manager.can_undo)

            choice = input("\nEnter your choice (0-13): ").strip()

            if choice == "1":
                handle_add_task(manager)
            elif choice == "2":
                render_tasks_table(manager.tasks, heading="ALL TASKS")
            elif choice == "3":
                handle_view_details(manager)
            elif choice == "4":
                handle_search(manager)
            elif choice == "5":
                handle_filter_and_sort(manager)
            elif choice == "6":
                handle_edit_task(manager)
            elif choice == "7":
                handle_toggle_status(manager)
            elif choice == "8":
                handle_delete_task(manager)
            elif choice == "9":
                handle_clear_completed(manager)
            elif choice == "10":
                render_dashboard(manager.get_statistics())
            elif choice == "11":
                handle_export_csv(manager)
            elif choice == "12":
                if manager.undo():
                    print_success("Reverted the last change!")
                else:
                    print_info("Nothing to undo.")
            elif choice == "13":
                handle_restore_backup(manager)
            elif choice == "0":
                print_success("Thank you for using To-Do List Manager. Goodbye!")
                break
            else:
                print_error("Invalid choice! Please enter a number from 0 to 13.")
    except (KeyboardInterrupt, EOFError):
        print()
        print_info("Exiting To-Do List Manager. Your saved tasks are safe.")


if __name__ == "__main__":
    run_app()

    new_priority = prompt_priority(existing["priority"], allow_keep=True)
    new_category = input(f"New category [{existing['category']}]: ").strip() or None
    new_due = prompt_due_date(existing.get("due_date"), allow_keep=True)

    current_tags = ", ".join(existing.get("tags", [])) or "None"
    new_tags_raw = input(f"New comma-separated tags (type '-' to clear, Enter to keep '{current_tags}'): ").strip()
    if not new_tags_raw:
        new_tags = None
    elif new_tags_raw == "-":
        new_tags = []
    else:
        new_tags = new_tags_raw

    try:
        updated = manager.edit_task(
            task_id,
            title=new_title or None,
            description=new_desc,
            priority=new_priority,
            category=new_category,
            due_date=new_due,  # type: ignore[arg-type]
            tags=new_tags,
        )
    except (KeyError, ValueError) as error:
        print_error(str(error))
        return

    print_success(f"Task #{updated['id']} updated successfully!")


def handle_toggle_status(manager: TodoManager) -> None:
    task_id = prompt_int("Enter Task ID to complete/reopen: ")
    if task_id is None:
        return
    task = manager.get_task(task_id)
    if not task:
        print_error(f"Task ID {task_id} not found!")
        return

    if task["completed"]:
        if prompt_confirm(f"Task #{task_id} is already completed. Reopen it?"):
            manager.reopen_task(task_id)
            print_success(f"Task #{task_id} reopened as pending!")
    else:
        manager.complete_task(task_id)
        print_success(f"Task #{task_id} marked as completed!")


def handle_delete_task(manager: TodoManager) -> None:
    task_id = prompt_int("Enter Task ID to delete: ")
    if task_id is None:
        return
    task = manager.get_task(task_id)
    if not task:
        print_error(f"Task ID {task_id} not found!")
        return
    if prompt_confirm(f"Delete task #{task_id} '{task['title']}'?"):
        manager.delete_task(task_id)
        print_success(f"Task #{task_id} deleted successfully!")
    else:
        print_info("Deletion cancelled.")


def handle_clear_completed(manager: TodoManager) -> None:
    completed_count = sum(1 for task in manager.tasks if task["completed"])
    if completed_count == 0:
        print_info("There are no completed tasks to clear.")
        return
    if prompt_confirm(f"Remove all {completed_count} completed task(s)?"):
        removed = manager.clear_completed()
        print_success(f"Removed {removed} completed task(s).")
    else:
        print_info("Operation cancelled.")


def handle_export_csv(manager: TodoManager) -> None:
    default_csv = DEFAULT_DATA_FILE.with_name("tasks_export.csv")
    raw_path = input(f"Enter CSV path [default: {default_csv.name}]: ").strip()
    target = Path(raw_path) if raw_path else default_csv
    if not target.is_absolute():
        target = DEFAULT_DATA_FILE.parent / target

    try:
        exported = manager.export_csv(target)
    except Exception as error:
        print_error(f"Failed to export CSV: {error}")
        return
    print_success(f"Exported {len(manager.tasks)} task(s) to '{exported}'.")


def handle_restore_backup(manager: TodoManager) -> None:
    backup_path = get_backup_path(manager.data_file)
    if not backup_path.exists():
        print_warning("No backup file exists yet. Backups are created automatically on updates.")
        return
    if prompt_confirm(f"Restore tasks from '{backup_path.name}'? Current unsaved view will be replaced"):
        try:
            restored = manager.restore_backup()
        except Exception as error:
            print_error(f"Backup restore failed: {error}")
            return
        print_success(f"Restored {len(restored)} task(s) from backup!")


def initialize_manager(data_file: Path = DEFAULT_DATA_FILE) -> TodoManager:
    """Initialize TodoManager, offering backup recovery if the main file is corrupted."""
    try:
        return TodoManager(data_file=data_file, auto_load=True)
    except RuntimeError as error:
        print_error(str(error))
        backup_path = get_backup_path(data_file)
        if backup_path.exists() and prompt_confirm("A backup exists. Restore from backup?"):
            manager = TodoManager(data_file=data_file, auto_load=False)
            restored = manager.restore_backup()
            print_success(f"Recovered {len(restored)} task(s) from backup!")
            return manager
        print_error("Please fix tasks.json before continuing.")
        raise SystemExit(1) from error


def run_app(data_file: Path = DEFAULT_DATA_FILE) -> None:
    """Run the interactive To-Do List Manager CLI loop."""
    configure_console()
    manager = initialize_manager(data_file=data_file)

    try:
        while True:
            stats = manager.get_statistics()
            print_banner(stats)
            print_menu(can_undo=manager.can_undo)

            choice = input("\nEnter your choice (0-13): ").strip()

            if choice == "1":
                handle_add_task(manager)
            elif choice == "2":
                render_tasks_table(manager.tasks, heading="ALL TASKS")
            elif choice == "3":
                handle_view_details(manager)
            elif choice == "4":
                handle_search(manager)
            elif choice == "5":
                handle_filter_and_sort(manager)
            elif choice == "6":
                handle_edit_task(manager)
            elif choice == "7":
                handle_toggle_status(manager)
            elif choice == "8":
                handle_delete_task(manager)
            elif choice == "9":
                handle_clear_completed(manager)
            elif choice == "10":
                render_dashboard(manager.get_statistics())
            elif choice == "11":
                handle_export_csv(manager)
            elif choice == "12":
                if manager.undo():
                    print_success("Reverted the last change!")
                else:
                    print_info("Nothing to undo.")
            elif choice == "13":
                handle_restore_backup(manager)
            elif choice == "0":
                print_success("Thank you for using To-Do List Manager. Goodbye!")
                break
            else:
                print_error("Invalid choice! Please enter a number from 0 to 13.")
    except (KeyboardInterrupt, EOFError):
        print()
        print_info("Exiting To-Do List Manager. Your saved tasks are safe.")


if __name__ == "__main__":
    run_app()

