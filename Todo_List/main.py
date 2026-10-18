
import todo

try:
    tasks = todo.load_tasks()
except RuntimeError as error:
    print(error)
    print("Please fix tasks.json before continuing.")
    raise SystemExit(1)


while True:
    print("\n===== TO-DO LIST APP =====")
    print("1. Add Task")
    print("2. View All Tasks")
    print("3. Mark Task as Completed")
    print("4. Delete Task")
    print("5. Exit")

    choice = input("Enter your choice: ").strip()

    if choice == "1":
        title = input("Enter task name: ")
        todo.add_task(tasks, title)

    elif choice == "2":
        todo.view_tasks(tasks)

    elif choice == "3":
        try:
            task_id = int(input("Enter Task ID: "))
            todo.complete_task(tasks, task_id)
        except ValueError:
            print("Please enter a valid numeric Task ID.")

    elif choice == "4":
        try:
            task_id = int(input("Enter Task ID to delete: "))
            todo.delete_task(tasks, task_id)
        except ValueError:
            print("Please enter a valid numeric Task ID.")

    elif choice == "5":
        print("Thank you for using To-Do List App!")
        break

    else:
        print("Invalid choice! Please enter 1 to 5.")
