
import json
from pathlib import Path
from datetime import date

DATA_FILE = Path(__file__).with_name("expenses.json")


def load_expenses():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            expenses = json.load(file)

        if not isinstance(expenses, list):
            raise ValueError("Expense data must be a list.")

        for expense in expenses:
            if not isinstance(expense, dict):
                raise ValueError("Invalid expense record.")
            if not {"id", "title", "amount", "category", "date"}.issubset(expense):
                raise ValueError("Expense record is incomplete.")

        return expenses

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Cannot read expenses.json: {error}"
        ) from error


def save_expenses(expenses):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(expenses, file, indent=4, ensure_ascii=False)


def add_expense(expenses, title, amount, category):
    title = title.strip()
    category = category.strip()

    if not title or not category:
        print("Title and category cannot be empty!")
        return

    if amount <= 0:
        print("Amount must be greater than zero!")
        return

    expense_id = max(
        (expense["id"] for expense in expenses),
        default=0
    ) + 1

    new_expense = {
        "id": expense_id,
        "title": title,
        "amount": round(amount, 2),
        "category": category,
        "date": date.today().isoformat()
    }

    expenses.append(new_expense)
    save_expenses(expenses)
    print("Expense added successfully!")


def view_expenses(expenses):
    if not expenses:
        print("\nNo expenses found.")
        return

    print("\n===== ALL EXPENSES =====")

    for expense in expenses:
        print(
            f"ID: {expense['id']} | "
            f"Title: {expense['title']} | "
            f"Amount: Rs. {expense['amount']:.2f} | "
            f"Category: {expense['category']} | "
            f"Date: {expense['date']}"
        )


def show_total(expenses):
    total = sum(expense["amount"] for expense in expenses)

    print(f"\nTotal Expenses: Rs. {total:.2f}")


def delete_expense(expenses, expense_id):
    for expense in expenses:
        if expense["id"] == expense_id:
            expenses.remove(expense)
            save_expenses(expenses)
            print("Expense deleted successfully!")
            return

    print("Expense ID not found!")


def show_category_totals(expenses):
    if not expenses:
        print("\nNo expenses found.")
        return

    totals = {}

    for expense in expenses:
        category = expense["category"]
        totals[category] = totals.get(category, 0) + expense["amount"]

    print("\n===== CATEGORY TOTALS =====")

    for category, amount in totals.items():
        print(f"{category}: Rs. {amount:.2f}")
