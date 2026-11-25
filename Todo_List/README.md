# To-Do List Manager

A modular, zero-dependency Python CLI To-Do List application with rich task metadata, atomic JSON persistence, automatic backups, search/filter/sort tools, undo support, CSV export, and a productivity dashboard.

## Project Structure

- `main.py` — Interactive terminal CLI loop and input handlers.
- `todo.py` — Core `TodoManager` class plus backward-compatible procedural task APIs (`load_tasks`, `save_tasks`, `add_task`, `view_tasks`, `complete_task`, `reopen_task`, `delete_task`).
- `models.py` — `Task` dataclass, field validation, priority/tag normalization, due-date and overdue calculations, and legacy record migration.
- `storage.py` — Atomic JSON saves, automatic `.backup.json` backups, backup recovery, and CSV export.
- `ui.py` — UTF-8 console configuration, ANSI color styling, Unicode task tables, task detail view, and productivity dashboard.
- `tasks.json` — Local JSON task storage file.
- `test_todo.py` — Unit and CLI smoke tests using Python's built-in `unittest` module.

## Features

- **Full Task Metadata**: Title, description, priority (`Low`, `Medium`, `High`, `Urgent`), category, `YYYY-MM-DD` due date, tags, and created/updated/completed timestamps.
- **Overdue Tracking**: Automatically highlights overdue pending tasks and tracks tasks due today.
- **Search, Filter & Sort**: Search across ID, title, description, category, and tags; filter by status, priority, category, tag, or overdue state; sort by ID, priority, due date, title, created time, or status.
- **Safe Persistence & Recovery**: Atomic temporary-file replacement prevents file corruption; updates automatically maintain `tasks.backup.json`, and in-session **Undo** lets you revert recent edits/deletes.
- **CSV Export & Analytics**: Export tasks to `tasks_export.csv` (UTF-8 with BOM for Excel compatibility) and inspect completion progress and breakdowns in the Productivity Dashboard.

## Usage

Run the application from either the workspace root or inside `Todo_List`:

```bash
python Todo_List/main.py
```

Run the test suite:

```bash
python -m unittest Todo_List/test_todo.py -v
```
