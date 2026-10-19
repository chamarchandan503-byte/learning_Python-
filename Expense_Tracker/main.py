
import expense

try:
    expenses = expense.load_expenses()
except RuntimeError as error:
    print(error)
    print("Please fix expenses.json before continuing.")
    raise SystemExit(1)


while True:
    print("\n===== EXPENSE TRACKER =====")
    print("1. Add Expense")
    print("2. View All Expenses")
    print("3. Show Total Expenses")
    print("4. Show Category Totals")
    print("5. Delete Expense")
    print("6. Exit")

    choice = input("Enter your choice: ").strip()

    if choice == "1":
        title = input("Enter expense name: ")
        category = input("Enter category (Food/Travel/Study/Other): ")

        try:
            amount = float(input("Enter amount in Rs.: "))
            expense.add_expense(
                expenses, title, amount, category
            )
        except ValueError:
            print("Please enter a valid amount.")

    elif choice == "2":
        expense.view_expenses(expenses)

    elif choice == "3":
        expense.show_total(expenses)

    elif choice == "4":
        expense.show_category_totals(expenses)

    elif choice == "5":
        try:
            expense_id = int(input("Enter Expense ID to delete: "))
            expense.delete_expense(expenses, expense_id)
        except ValueError:
            print("Please enter a valid numeric ID.")

    elif choice == "6":
        print("Thank you for using Expense Tracker!")
        break

    else:
        print("Invalid choice! Please enter 1 to 6.")
