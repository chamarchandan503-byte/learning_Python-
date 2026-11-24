# 🏧 Professional Mini ATM System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-modular%20OOP-orange.svg)]()
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)]()

A modern, production-grade CLI ATM (Automated Teller Machine) banking application written in Python. Built with clean Object-Oriented Design (OOP), multi-account persistence via JSON, secure PIN authentication, peer-to-peer transfers, mini-statements, and printable ASCII receipts.

---

## 🌟 Key Features

- **🔐 Secure Authentication & PIN Lockout**:
  - 4-digit PIN verification.
  - Multi-attempt protection: Locks card after 3 consecutive failed PIN attempts to prevent brute-force.
  - Self-service **PIN Change** with current PIN verification.

- **💼 Multi-Account & Data Persistence**:
  - Real-time persistent state stored in `data.json`.
  - Atomic write operations prevent file corruption during crashes or interruptions.
  - Automatic database self-healing if files are missing or malformed.

- **💰 Comprehensive Banking Operations**:
  - **Balance Inquiry**: View ledger balance, available cash, and remaining daily limits.
  - **Cash Deposit**: Deposit funds with real-time balance update.
  - **Cash Withdrawal**: ATM denomination checks (multiples of ₹100), overdraw protection, and daily limit enforcement.
  - **⚡ Quick Cash**: One-click fast withdrawals (₹500, ₹1,000, ₹2,000, ₹5,000, ₹10,000).
  - **🔄 Peer-to-Peer Fund Transfer**: Instantly transfer money between accounts with dual ledger logging.

- **📜 Statements & Printable Receipts**:
  - **Mini-Statement**: Formatted tabular view of recent transactions with timestamps and unique Transaction IDs (`TXN...`).
  - **Digital Receipts**: Beautiful ASCII slip generated after each transaction or on-demand.

- **🎨 Professional Terminal User Interface**:
  - ANSI-styled interface with interactive prompts, clean borders, and clear screens.
  - Safe user input handling (no crashes on invalid numbers, negative inputs, or `Ctrl+C`).

---

## 📂 Project Structure

```text
MINI_ATM/
├── main.py          # Customer-facing interactive ATM CLI application
├── bank.py          # Core banking engine, account models, and persistence layer
├── transaction.py   # Transaction models, mini-statement & receipt formatting
├── data.json        # Persistent JSON account & transaction database
├── test_atm.py      # Automated unit test suite (6 passing test cases)
└── README.md        # Comprehensive project documentation
```

---

## 🔑 Demo Account Credentials

The system comes pre-configured with two demo accounts for testing deposits, withdrawals, and peer-to-peer transfers:

| Account Number | Account Holder | PIN | Initial Balance | Daily ATM Limit |
| :--- | :--- | :--- | :--- | :--- |
| **`1001`** *(Default)* | Chandan Rao | **`1234`** | ₹25,000.00 | ₹50,000.00 |
| **`1002`** | Rahul Sharma | **`5678`** | ₹15,000.00 | ₹50,000.00 |

> **Tip**: When prompted for an account number during login, you can simply press **Enter** to quickly select the default demo account `1001`.

---

## 🚀 How to Run the Application

### 1. Open Terminal in Project Directory
Navigate to the project folder:
```powershell
cd c:\Users\ChandanRao\Desktop\python\MINI_ATM
```

### 2. Launch the ATM
Run with Python:
```powershell
python main.py
```
*(Or use `py main.py` on Windows)*

---

## 🧪 Running Automated Tests

Run the test suite to verify all business rules, limits, transfers, and security validations:

```powershell
python test_atm.py
```

Expected output:
```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.002s

OK
```

---

## 🔧 Troubleshooting: `'python' is not recognized`

If you encounter:
```text
python : The term 'python' is not recognized as the name of a cmdlet...
```

### Quick Fix:
1. **Restart your terminal** or VS Code:
   Python has been added to your Windows User Environment Variables (`PATH`). Opening a fresh terminal will automatically load the updated PATH.
2. **Or refresh the PATH in your current PowerShell session**:
   ```powershell
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
   python --version
   ```

---

## 🏛️ Code Architecture & Design Highlights

- **`transaction.py`**:
  - `Transaction` dataclass with serialization (`to_dict` / `from_dict`).
  - `format_receipt()`: Generates ASCII transaction slips with masked account numbers (`XXXX-1001`).
  - `display_mini_statement()`: Formats transactions in a clean tabular view.
  - Maintains backward compatibility with legacy `add_transaction()` and `show_transactions()`.

- **`bank.py`**:
  - `BankAccount`: Enforces domain rules (positive amounts, multiples of 100, daily limits, balance checks).
  - `BankSystem`: Manages JSON storage with atomic file writing (`.tmp` -> replace) to prevent data corruption.
  - Backward-compatible wrappers for legacy functions: `check_balance()`, `deposit_money()`, `withdraw_money()`.

- **`main.py`**:
  - `ATMApplication`: Implements the menu loop, session state, clear screen transitions, and graceful `KeyboardInterrupt` handling.

---

## 📜 License & Credits
Developed as an educational and demonstration banking project. Free to modify and distribute.

---

## 🏛️ Code Architecture & Design Highlights

- **`transaction.py`**:
  - `Transaction` dataclass with serialization (`to_dict` / `from_dict`).
  - `format_receipt()`: Generates ASCII transaction slips with masked account numbers (`XXXX-1001`).
  - `display_mini_statement()`: Formats transactions in a clean tabular view.
  - Maintains backward compatibility with legacy `add_transaction()` and `show_transactions()`.

- **`bank.py`**:
  - `BankAccount`: Enforces domain rules (positive amounts, multiples of 100, daily limits, balance checks).
  - `BankSystem`: Manages JSON storage with atomic file writing (`.tmp` -> replace) to prevent data corruption.
  - Backward-compatible wrappers for legacy functions: `check_balance()`, `deposit_money()`, `withdraw_money()`.

- **`main.py`**:
  - `ATMApplication`: Implements the menu loop, session state, clear screen transitions, and graceful `KeyboardInterrupt` handling.

---

## 📜 License & Credits
Developed as an educational and demonstration banking project. Free to modify and distribute.

