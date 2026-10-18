
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("tasks.json")


def load_tasks():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            tasks = json.load(file)

        if not isinstance(tasks, list):
            raise ValueError("Tasks data must be a list.")

        for task in tasks:
            if not isinstance(task, dict):
                raise ValueError("Invalid task record.")
            if not {"id", "title", "completed"}.issubset(task):
                raise ValueError("Task record is incomplete.")

        return tasks

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Cannot read tasks.json: {error}"
        ) from error


def save_tasks(tasks):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=4, ensure_ascii=False)


def add_task(tasks, title):
    title = title.strip()

    if not title:
        print("Task name cannot be empty!")
        return

    task_id = max((task["id"] for task in tasks), default=0) + 1

    task = {
        "id": task_id,
        "title": title,
        "completed": False
    }

    tasks.append(task)
    save_tasks(tasks)
    print("Task added successfully!")


def view_tasks(tasks):
    if not tasks:
        print("\nNo tasks found. Add a new task first.")
        return

    print("\n===== YOUR TASKS =====")

    for task in tasks:
        status = "Completed" if task["completed"] else "Pending"
        print(f"ID: {task['id']} | {task['title']} | {status}")


def complete_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            if task["completed"]:
                print("This task is already completed.")
                return

            task["completed"] = True
            save_tasks(tasks)
            print("Task marked as completed!")
            return

    print("Task ID not found!")


def delete_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            save_tasks(tasks)
            print("Task deleted successfully!")
            return

    print("Task ID not found!")
