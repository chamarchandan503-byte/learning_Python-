# 🏧 Mini ATM System Using Python

## 📌 Project Description
Mini ATM System is a beginner-friendly Python project that simulates basic ATM operations. It allows users to check their balance, deposit money, withdraw money, and view transaction history.

The project uses JSON file handling to store account balance and transaction records between program runs.

## ✨ Features
- PIN-based login (demo PIN: `1234`)
- Check account balance
- Deposit money
- Withdraw money
- View transaction history
- Validate amounts and prevent withdrawals exceeding the balance
- Store account data in a JSON file

## 🛠️ Technologies Used
- Python 3
- JSON
- File Handling
- Functions
- Exception Handling

## 📂 Project Structure

```text
Project_01_Mini_ATM/
├── main.py
├── bank.py
├── transactions.py
├── data.json
└── README.md
```

## 💻 Requirements
- Python 3 installed
- Visual Studio Code (recommended)

No external Python libraries are required.

## 🚀 How to Run

1. Download or clone this project.
2. Open the project folder in VS Code.
3. Open the terminal.
4. Run the following command:

```bash
python main.py
```

On Windows, you can also use:

```powershell
py main.py
```

5. Enter the demo PIN: `1234`.
6. Select an option from the ATM menu.

## 📋 ATM Menu
1. Check Balance
2. Deposit Money
3. Withdraw Money
4. Transaction History
5. Exit

## 💾 Data Storage
The `data.json` file stores the current demo balance and transaction history. Keep this file in the project folder so the program can load the saved data.

## 🎯 Learning Objectives
This project demonstrates:
- Variables and data types
- Conditional statements
- Loops
- Functions
- Python modules and imports
- JSON data handling
- Exception handling
- Basic input validation

## ⚠️ Disclaimer
This project is created for educational purposes only. It is not a real banking application. The demo PIN is stored in the source code, and the JSON file is not secure storage. Do not use real banking credentials or sensitive financial information.

## 👨‍💻 Author
Created as a Python learning project.
