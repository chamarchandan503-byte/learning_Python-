"""
Banking Operations and Core Business Logic for Mini ATM System.

Manages account states, balance calculations, PIN authentication,
fund deposits, cash withdrawals, peer transfers, and JSON data persistence.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

from transaction import Transaction, create_transaction, add_transaction as legacy_add_tx


# Default data file path adjacent to this module
DATA_FILE_PATH = Path(__file__).resolve().parent / "data.json"


class BankAccount:
    """Represents a customer's bank account with balance and transaction history."""

    def __init__(
        self,
        account_number: str,
        holder_name: str,
        pin: str,
        balance: float = 0.0,
        daily_limit: float = 50000.0,
        withdrawn_today: float = 0.0,
        is_active: bool = True,
        transactions: Optional[List[Transaction]] = None,
    ):
        self.account_number = str(account_number)
        self.holder_name = holder_name
        self.pin = str(pin)
        self.balance = round(float(balance), 2)
        self.daily_limit = round(float(daily_limit), 2)
        self.withdrawn_today = round(float(withdrawn_today), 2)
        self.is_active = is_active
        self.transactions: List[Transaction] = transactions if transactions is not None else []

    def verify_pin(self, input_pin: str) -> bool:
        """Verify whether the provided PIN matches."""
        return self.pin == str(input_pin).strip()

    def change_pin(self, old_pin: str, new_pin: str) -> Tuple[bool, str]:
        """
        Change account PIN with verification and validation.
        """
        if not self.verify_pin(old_pin):
            return False, "Current PIN verification failed."

        cleaned_pin = str(new_pin).strip()
        if len(cleaned_pin) != 4 or not cleaned_pin.isdigit():
            return False, "New PIN must be exactly 4 numeric digits."

        if cleaned_pin == self.pin:
            return False, "New PIN cannot be identical to your current PIN."

        self.pin = cleaned_pin
        txn = create_transaction("PIN_CHANGE", 0.0, self.balance, "ATM PIN Changed Successfully")
        self.transactions.append(txn)
        return True, "PIN changed successfully! Please remember your new PIN."

    def deposit(self, amount: float, description: str = "") -> Tuple[bool, str, Optional[Transaction]]:
        """
        Deposit positive amount into the account.
        """
        if amount <= 0:
            return False, "Deposit amount must be greater than zero.", None

        if amount > 500000:
            return False, "Maximum deposit limit per transaction is Rs. 500,000.00", None

        self.balance = round(self.balance + amount, 2)
        desc = description or f"Deposited Rs. {amount:.2f} via ATM"
        txn = create_transaction("DEPOSIT", amount, self.balance, desc)
        self.transactions.append(txn)

        # Update legacy memory buffer as well
        legacy_add_tx("DEPOSIT", amount, self.balance)

        return True, f"Rs. {amount:.2f} deposited successfully!", txn

    def withdraw(self, amount: float, description: str = "") -> Tuple[bool, str, Optional[Transaction]]:
        """
        Withdraw amount from the account after balance and limit verification.
        """
        if amount <= 0:
            return False, "Withdrawal amount must be greater than zero.", None

        if amount % 100 != 0:
            return False, "Amount must be in multiples of Rs. 100 (e.g., 500, 1000, 2000).", None

        if amount > self.balance:
            return False, f"Insufficient balance! Available balance is Rs. {self.balance:.2f}.", None

        if (self.withdrawn_today + amount) > self.daily_limit:
            remaining_limit = max(0.0, self.daily_limit - self.withdrawn_today)
            return False, (
                f"Daily withdrawal limit exceeded! "
                f"Remaining limit today: Rs. {remaining_limit:.2f}."
            ), None

        self.balance = round(self.balance - amount, 2)
        self.withdrawn_today = round(self.withdrawn_today + amount, 2)
        desc = description or f"Withdrawn Rs. {amount:.2f} from ATM"
        txn = create_transaction("WITHDRAWAL", amount, self.balance, desc)
        self.transactions.append(txn)

        # Update legacy memory buffer as well
        legacy_add_tx("WITHDRAWAL", amount, self.balance)

        return True, f"Please collect your cash: Rs. {amount:.2f}", txn

    def transfer_to(
        self,
        target_account: BankAccount,
        amount: float
    ) -> Tuple[bool, str, Optional[Tuple[Transaction, Transaction]]]:
        """
        Transfer funds from this account to a destination account.
        """
        if self.account_number == target_account.account_number:
            return False, "Cannot transfer funds to the same account.", None

        if not target_account.is_active:
            return False, "Recipient account is currently inactive or restricted.", None

        if amount <= 0:
            return False, "Transfer amount must be greater than zero.", None

        if amount > self.balance:
            return False, f"Insufficient balance! Available balance is Rs. {self.balance:.2f}.", None

        # Debit source account
        self.balance = round(self.balance - amount, 2)
        debit_txn = create_transaction(
            "TRANSFER_SENT",
            amount,
            self.balance,
            f"Transferred to A/C {target_account.account_number} ({target_account.holder_name})"
        )
        self.transactions.append(debit_txn)

        # Credit target account
        target_account.balance = round(target_account.balance + amount, 2)
        credit_txn = create_transaction(
            "TRANSFER_RECEIVED",
            amount,
            target_account.balance,
            f"Received from A/C {self.account_number} ({self.holder_name})"
        )
        target_account.transactions.append(credit_txn)

        return True, f"Successfully transferred Rs. {amount:.2f} to {target_account.holder_name}!", (debit_txn, credit_txn)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize BankAccount instance to dictionary."""
        return {
            "account_number": self.account_number,
            "holder_name": self.holder_name,
            "pin": self.pin,
            "balance": self.balance,
            "daily_limit": self.daily_limit,
            "withdrawn_today": self.withdrawn_today,
            "is_active": self.is_active,
            "transactions": [t.to_dict() for t in self.transactions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BankAccount:
        """Create BankAccount instance from dictionary."""
        tx_list = [Transaction.from_dict(t) for t in data.get("transactions", [])]
        return cls(
            account_number=str(data.get("account_number", "")),
            holder_name=data.get("holder_name", "Customer"),
            pin=str(data.get("pin", "1234")),
            balance=float(data.get("balance", 0.0)),
            daily_limit=float(data.get("daily_limit", 50000.0)),
            withdrawn_today=float(data.get("withdrawn_today", 0.0)),
            is_active=bool(data.get("is_active", True)),
            transactions=tx_list
        )


class BankSystem:
    """Manages bank database, customer accounts, and file persistence."""

    def __init__(self, data_file: Path = DATA_FILE_PATH):
        self.data_file = Path(data_file)
        self.accounts: Dict[str, BankAccount] = {}
        self.load_data()

    def _get_default_accounts(self) -> Dict[str, BankAccount]:
        """Provide robust fallback accounts if data file does not exist."""
        acc1 = BankAccount(
            account_number="1001",
            holder_name="Chandan Rao",
            pin="1234",
            balance=25000.0,
            daily_limit=50000.0,
            withdrawn_today=0.0,
            is_active=True,
            transactions=[
                create_transaction("DEPOSIT", 25000.0, 25000.0, "Initial Account Deposit")
            ]
        )
        acc2 = BankAccount(
            account_number="1002",
            holder_name="Rahul Sharma",
            pin="5678",
            balance=15000.0,
            daily_limit=50000.0,
            withdrawn_today=0.0,
            is_active=True,
            transactions=[
                create_transaction("DEPOSIT", 15000.0, 15000.0, "Initial Account Deposit")
            ]
        )
        return {"1001": acc1, "1002": acc2}

    def load_data(self) -> bool:
        """
        Load account data from JSON file with error-recovery fallback.
        """
        if not self.data_file.exists():
            self.accounts = self._get_default_accounts()
            self.save_data()
            return True

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            accounts_data = data.get("accounts", {})
            if not accounts_data and "balance" in data:
                # Handle legacy schema {"balance": 5000, "transactions": []}
                default_acc = BankAccount(
                    account_number="1001",
                    holder_name="Chandan Rao",
                    pin="1234",
                    balance=float(data.get("balance", 5000.0)),
                    daily_limit=50000.0,
                    withdrawn_today=0.0,
                    is_active=True,
                    transactions=[]
                )
                self.accounts = {"1001": default_acc}
                self.save_data()
                return True

            self.accounts = {}
            for acc_num, acc_info in accounts_data.items():
                self.accounts[str(acc_num)] = BankAccount.from_dict(acc_info)

            return True

        except (json.JSONDecodeError, OSError) as err:
            print(f"[Warning] Could not read {self.data_file.name} ({err}). Initializing default records.")
            self.accounts = self._get_default_accounts()
            self.save_data()
            return False

    def save_data(self) -> bool:
        """
        Safely persist account records to JSON using atomic write semantics.
        """
        try:
            payload = {
                "accounts": {
                    acc_num: acc.to_dict() for acc_num, acc in self.accounts.items()
                }
            }

            temp_file = self.data_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            # Atomic rename / replace
            temp_file.replace(self.data_file)
            return True
        except OSError as err:
            print(f"[Error] Failed to persist data to {self.data_file}: {err}")
            return False

    def authenticate(self, account_number: str, pin: str) -> Tuple[bool, str, Optional[BankAccount]]:
        """
        Authenticate an account using Account Number and PIN.
        """
        acc = self.accounts.get(str(account_number).strip())
        if not acc:
            return False, "Account number not found.", None

        if not acc.is_active:
            return False, "This account is blocked or inactive.", None

        if not acc.verify_pin(pin):
            return False, "Incorrect PIN! Access denied.", None

        return True, f"Welcome back, {acc.holder_name}!", acc

    def find_account_by_pin(self, pin: str) -> Optional[BankAccount]:
        """
        Search for an active account matching the given PIN (useful for 1-step demo login).
        """
        cleaned_pin = str(pin).strip()
        for acc in self.accounts.values():
            if acc.is_active and acc.pin == cleaned_pin:
                return acc
        return None

    def get_account(self, account_number: str) -> Optional[BankAccount]:
        """Look up an account by account number."""
        return self.accounts.get(str(account_number).strip())


# ---------------------------------------------------------
# Singleton System Instance & Backward Compatibility
# ---------------------------------------------------------
bank_system = BankSystem()


def get_default_account() -> BankAccount:
    """Return the primary demo account (1001)."""
    acc = bank_system.get_account("1001")
    if not acc:
        acc = next(iter(bank_system.accounts.values()))
    return acc


# Dynamic balance getter/setter compatibility
balance = get_default_account().balance


def check_balance() -> float:
    """Display current bank balance (Legacy API)."""
    acc = get_default_account()
    print(f"Your Current Balance: Rs. {acc.balance:.2f}")
    return acc.balance


def deposit_money(amount: float) -> bool:
    """Deposit money into the primary account (Legacy API)."""
    acc = get_default_account()
    success, message, _ = acc.deposit(amount)
    print(message)
    if success:
        bank_system.save_data()
        print(f"New Balance: Rs. {acc.balance:.2f}")
    return success


def withdraw_money(amount: float) -> bool:
    """Withdraw money from the primary account (Legacy API)."""
    acc = get_default_account()
    success, message, _ = acc.withdraw(amount)
    print(message)
    if success:
        bank_system.save_data()
        print(f"Remaining Balance: Rs. {acc.balance:.2f}")
    return success

    def deposit(self, amount: float, description: str = "") -> Tuple[bool, str, Optional[Transaction]]:
        """
        Deposit positive amount into the account.
        """
        if amount <= 0:
            return False, "Deposit amount must be greater than zero.", None

        if amount > 500000:
            return False, "Maximum deposit limit per transaction is Rs. 500,000.00", None

        self.balance = round(self.balance + amount, 2)
        desc = description or f"Deposited Rs. {amount:.2f} via ATM"
        txn = create_transaction("DEPOSIT", amount, self.balance, desc)
        self.transactions.append(txn)

        # Update legacy memory buffer as well
        legacy_add_tx("DEPOSIT", amount, self.balance)

        return True, f"Rs. {amount:.2f} deposited successfully!", txn

    def withdraw(self, amount: float, description: str = "") -> Tuple[bool, str, Optional[Transaction]]:
        """
        Withdraw amount from the account after balance and limit verification.
        """
        if amount <= 0:
            return False, "Withdrawal amount must be greater than zero.", None

        if amount % 100 != 0:
            return False, "Amount must be in multiples of Rs. 100 (e.g., 500, 1000, 2000).", None

        if amount > self.balance:
            return False, f"Insufficient balance! Available balance is Rs. {self.balance:.2f}.", None

        if (self.withdrawn_today + amount) > self.daily_limit:
            remaining_limit = max(0.0, self.daily_limit - self.withdrawn_today)
            return False, (
                f"Daily withdrawal limit exceeded! "
                f"Remaining limit today: Rs. {remaining_limit:.2f}."
            ), None

        self.balance = round(self.balance - amount, 2)
        self.withdrawn_today = round(self.withdrawn_today + amount, 2)
        desc = description or f"Withdrawn Rs. {amount:.2f} from ATM"
        txn = create_transaction("WITHDRAWAL", amount, self.balance, desc)
        self.transactions.append(txn)

        # Update legacy memory buffer as well
        legacy_add_tx("WITHDRAWAL", amount, self.balance)

        return True, f"Please collect your cash: Rs. {amount:.2f}", txn

    def transfer_to(
        self,
        target_account: BankAccount,
        amount: float
    ) -> Tuple[bool, str, Optional[Tuple[Transaction, Transaction]]]:
        """
        Transfer funds from this account to a destination account.
        """
        if self.account_number == target_account.account_number:
            return False, "Cannot transfer funds to the same account.", None

        if not target_account.is_active:
            return False, "Recipient account is currently inactive or restricted.", None

        if amount <= 0:
            return False, "Transfer amount must be greater than zero.", None

        if amount > self.balance:
            return False, f"Insufficient balance! Available balance is Rs. {self.balance:.2f}.", None

        # Debit source account
        self.balance = round(self.balance - amount, 2)
        debit_txn = create_transaction(
            "TRANSFER_SENT",
            amount,
            self.balance,
            f"Transferred to A/C {target_account.account_number} ({target_account.holder_name})"
        )
        self.transactions.append(debit_txn)

        # Credit target account
        target_account.balance = round(target_account.balance + amount, 2)
        credit_txn = create_transaction(
            "TRANSFER_RECEIVED",
            amount,
            target_account.balance,
            f"Received from A/C {self.account_number} ({self.holder_name})"
        )
        target_account.transactions.append(credit_txn)

        return True, f"Successfully transferred Rs. {amount:.2f} to {target_account.holder_name}!", (debit_txn, credit_txn)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize BankAccount instance to dictionary."""
        return {
            "account_number": self.account_number,
            "holder_name": self.holder_name,
            "pin": self.pin,
            "balance": self.balance,
            "daily_limit": self.daily_limit,
            "withdrawn_today": self.withdrawn_today,
            "is_active": self.is_active,
            "transactions": [t.to_dict() for t in self.transactions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BankAccount:
        """Create BankAccount instance from dictionary."""
        tx_list = [Transaction.from_dict(t) for t in data.get("transactions", [])]
        return cls(
            account_number=str(data.get("account_number", "")),
            holder_name=data.get("holder_name", "Customer"),
            pin=str(data.get("pin", "1234")),
            balance=float(data.get("balance", 0.0)),
            daily_limit=float(data.get("daily_limit", 50000.0)),
            withdrawn_today=float(data.get("withdrawn_today", 0.0)),
            is_active=bool(data.get("is_active", True)),
            transactions=tx_list
        )


class BankSystem:
    """Manages bank database, customer accounts, and file persistence."""

    def __init__(self, data_file: Path = DATA_FILE_PATH):
        self.data_file = Path(data_file)
        self.accounts: Dict[str, BankAccount] = {}
        self.load_data()

    def _get_default_accounts(self) -> Dict[str, BankAccount]:
        """Provide robust fallback accounts if data file does not exist."""
        acc1 = BankAccount(
            account_number="1001",
            holder_name="Chandan Rao",
            pin="1234",
            balance=25000.0,
            daily_limit=50000.0,
            withdrawn_today=0.0,
            is_active=True,
            transactions=[
                create_transaction("DEPOSIT", 25000.0, 25000.0, "Initial Account Deposit")
            ]
        )
        acc2 = BankAccount(
            account_number="1002",
            holder_name="Rahul Sharma",
            pin="5678",
            balance=15000.0,
            daily_limit=50000.0,
            withdrawn_today=0.0,
            is_active=True,
            transactions=[
                create_transaction("DEPOSIT", 15000.0, 15000.0, "Initial Account Deposit")
            ]
        )
        return {"1001": acc1, "1002": acc2}

    def load_data(self) -> bool:
        """
        Load account data from JSON file with error-recovery fallback.
        """
        if not self.data_file.exists():
            self.accounts = self._get_default_accounts()
            self.save_data()
            return True

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            accounts_data = data.get("accounts", {})
            if not accounts_data and "balance" in data:
                # Handle legacy schema {"balance": 5000, "transactions": []}
                default_acc = BankAccount(
                    account_number="1001",
                    holder_name="Chandan Rao",
                    pin="1234",
                    balance=float(data.get("balance", 5000.0)),
                    daily_limit=50000.0,
                    withdrawn_today=0.0,
                    is_active=True,
                    transactions=[]
                )
                self.accounts = {"1001": default_acc}
                self.save_data()
                return True

            self.accounts = {}
            for acc_num, acc_info in accounts_data.items():
                self.accounts[str(acc_num)] = BankAccount.from_dict(acc_info)

            return True

        except (json.JSONDecodeError, OSError) as err:
            print(f"[Warning] Could not read {self.data_file.name} ({err}). Initializing default records.")
            self.accounts = self._get_default_accounts()
            self.save_data()
            return False

    def save_data(self) -> bool:
        """
        Safely persist account records to JSON using atomic write semantics.
        """
        try:
            payload = {
                "accounts": {
                    acc_num: acc.to_dict() for acc_num, acc in self.accounts.items()
                }
            }

            temp_file = self.data_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            # Atomic rename / replace
            temp_file.replace(self.data_file)
            return True
        except OSError as err:
            print(f"[Error] Failed to persist data to {self.data_file}: {err}")
            return False

    def authenticate(self, account_number: str, pin: str) -> Tuple[bool, str, Optional[BankAccount]]:
        """
        Authenticate an account using Account Number and PIN.
        """
        acc = self.accounts.get(str(account_number).strip())
        if not acc:
            return False, "Account number not found.", None

        if not acc.is_active:
            return False, "This account is blocked or inactive.", None

        if not acc.verify_pin(pin):
            return False, "Incorrect PIN! Access denied.", None

        return True, f"Welcome back, {acc.holder_name}!", acc

    def find_account_by_pin(self, pin: str) -> Optional[BankAccount]:
        """
        Search for an active account matching the given PIN (useful for 1-step demo login).
        """
        cleaned_pin = str(pin).strip()
        for acc in self.accounts.values():
            if acc.is_active and acc.pin == cleaned_pin:
                return acc
        return None

    def get_account(self, account_number: str) -> Optional[BankAccount]:
        """Look up an account by account number."""
        return self.accounts.get(str(account_number).strip())


# ---------------------------------------------------------
# Singleton System Instance & Backward Compatibility
# ---------------------------------------------------------
bank_system = BankSystem()


def get_default_account() -> BankAccount:
    """Return the primary demo account (1001)."""
    acc = bank_system.get_account("1001")
    if not acc:
        acc = next(iter(bank_system.accounts.values()))
    return acc


# Dynamic balance getter/setter compatibility
balance = get_default_account().balance


def check_balance() -> float:
    """Display current bank balance (Legacy API)."""
    acc = get_default_account()
    print(f"Your Current Balance: Rs. {acc.balance:.2f}")
    return acc.balance


def deposit_money(amount: float) -> bool:
    """Deposit money into the primary account (Legacy API)."""
    acc = get_default_account()
    success, message, _ = acc.deposit(amount)
    print(message)
    if success:
        bank_system.save_data()
        print(f"New Balance: Rs. {acc.balance:.2f}")
    return success


def withdraw_money(amount: float) -> bool:
    """Withdraw money from the primary account (Legacy API)."""
    acc = get_default_account()
    success, message, _ = acc.withdraw(amount)
    print(message)
    if success:
        bank_system.save_data()
        print(f"Remaining Balance: Rs. {acc.balance:.2f}")
    return success

