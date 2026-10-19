# Expense Tracker in Python

## Project Description
Expense Tracker is a simple Python application that helps users record and manage their daily expenses. Users can add expenses, view all records, calculate total spending, check category-wise totals, and delete expenses. All expense records are stored in a JSON file.

## Features
- Add a new expense.
- View all expenses.
- Calculate total expenses.
- View category-wise spending.
- Delete an expense by ID.
- Automatically record the current date.
- Save expense data in a JSON file.
- Validate user input.

## Technologies Used
- Python
- JSON
- `datetime` module
- `pathlib` module
- VS Code

## Project Structure
```text
Project_06_Expense_Tracker/
│
├── main.py
├── expense.py
├── expenses.json
└── README.md
```

## Requirements
- Python 3 installed on your computer.
- Visual Studio Code (recommended).

No external libraries are required.

## How to Run
1. Download or clone the project.
2. Open the project folder in VS Code.
3. Make sure `expenses.json` contains an empty list (`[]`) when starting with no records.
4. Open the terminal.
5. Run the following command:

```bash
python main.py
```

6. Select an option from the menu to manage your expenses.

## Example Output
```text
===== EXPENSE TRACKER =====
1. Add Expense
2. View All Expenses
3. Show Total Expenses
4. Show Category Totals
5. Delete Expense
6. Exit

Enter your choice: 1
Enter expense name: Lunch
Enter category: Food
Enter amount in Rs.: 120
Expense added successfully!
```

## Learning Objectives
- Understand Python functions and loops.
- Work with lists and dictionaries.
- Read and write JSON files.
- Use the `datetime` and `pathlib` modules.
- Calculate total and category-wise expenses.
- Handle invalid input using `try-except`.

## Future Improvements
- Add a monthly expense report.
- Set a monthly budget limit.
- Display expense charts.
- Add a graphical user interface (GUI).
- Export expense reports to CSV.

## Data and Privacy
Expense records are stored locally in `expenses.json`. Avoid adding sensitive financial information if you plan to share this project publicly on GitHub.

## Author
Python Beginner Project

## Project Status
Completed — Basic Version
