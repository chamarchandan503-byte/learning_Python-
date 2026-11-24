"""
Transaction Management Module for Mini ATM System.

Handles transaction models, history logging, mini-statement formatting,
and professional digital receipt generation.
"""

from __future__ import annotations
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class Transaction:
    """Represents an individual financial transaction."""

    txn_id: str
    timestamp: str
    type: str  # DEPOSIT, WITHDRAWAL, TRANSFER_SENT, TRANSFER_RECEIVED, PIN_CHANGE
    amount: float
    balance_after: float
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction instance to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Transaction:
        """Create a Transaction instance from a dictionary."""
        return cls(
            txn_id=data.get("txn_id", generate_txn_id()),
            timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            type=data.get("type", "UNKNOWN"),
            amount=float(data.get("amount", 0.0)),
            balance_after=float(data.get("balance_after", 0.0)),
            description=data.get("description", "")
        )


def generate_txn_id(prefix: str = "TXN") -> str:
    """Generate a unique transaction identifier."""
    time_part = datetime.now().strftime("%Y%m%d%H%M%S")
    rand_part = uuid.uuid4().hex[:4].upper()
    return f"{prefix}{time_part}{rand_part}"


def create_transaction(
    txn_type: str,
    amount: float,
    balance_after: float,
    description: str = ""
) -> Transaction:
    """Factory function to instantiate a new Transaction with current timestamp."""
    return Transaction(
        txn_id=generate_txn_id(),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        type=txn_type.upper(),
        amount=round(float(amount), 2),
        balance_after=round(float(balance_after), 2),
        description=description
    )


def format_receipt(
    transaction: Transaction,
    account_number: str,
    holder_name: str,
    bank_name: str = "APEX GLOBAL MINI ATM"
) -> str:
    """
    Format a transaction into a professional ASCII printed receipt.
    """
    masked_acc = f"XXXX-{account_number[-4:]}" if len(account_number) >= 4 else account_number
    border = "═" * 46
    divider = "─" * 46

    receipt_lines = [
        f"╔{border}╗",
        f"║{bank_name.center(46)}║",
        f"║{'TRANSACTION RECEIPT'.center(46)}║",
        f"╠{border}╣",
        f"║ Date & Time    : {transaction.timestamp:<27}║",
        f"║ Txn ID         : {transaction.txn_id:<27}║",
        f"║ Account Number : {masked_acc:<27}║",
        f"║ Account Holder : {holder_name[:25]:<27}║",
        f"╟{divider}╢",
        f"║ Txn Type       : {transaction.type:<27}║",
        f"║ Txn Amount     : Rs. {transaction.amount:>10.2f}{'':<13}║",
        f"║ Available Bal  : Rs. {transaction.balance_after:>10.2f}{'':<13}║",
        f"║ Status         : {'SUCCESS (COMPLETED)':<27}║",
    ]

    if transaction.description:
        desc = (transaction.description[:25] + "..") if len(transaction.description) > 27 else transaction.description
        receipt_lines.append(f"║ Note           : {desc:<27}║")

    receipt_lines.extend([
        f"╠{border}╣",
        f"║{'Thank You For Banking With Us!'.center(46)}║",
        f"║{'Please Retain This Receipt'.center(46)}║",
        f"╚{border}╝"
    ])

    return "\n".join(receipt_lines)


def display_mini_statement(
    transactions: List[Transaction],
    account_number: str,
    holder_name: str,
    limit: int = 5
) -> str:
    """
    Generate a clean tabular representation of recent transactions.
    """
    masked_acc = f"XXXX-{account_number[-4:]}" if len(account_number) >= 4 else account_number
    header = (
        f"\n{'=' * 72}\n"
        f"                    MINI STATEMENT (LAST {limit} TRANSACTIONS)\n"
        f" Account: {masked_acc} | Name: {holder_name}\n"
        f"{'=' * 72}\n"
        f"{'Txn ID':<16} | {'Date & Time':<19} | {'Type':<12} | {'Amount (Rs)':>10} | {'Balance':>10}\n"
        f"{'-' * 72}"
    )

    if not transactions:
        return f"{header}\n                      No transactions found.\n{'=' * 72}"

    recent = transactions[-limit:]
    rows = []
    for txn in reversed(recent):
        rows.append(
            f"{txn.txn_id:<16} | {txn.timestamp:<19} | {txn.type:<12} | "
            f"{txn.amount:>10.2f} | {txn.balance_after:>10.2f}"
        )

    footer = f"{'=' * 72}\n"
    return "\n".join([header] + rows + [footer])


# ---------------------------------------------------------
# Backward Compatibility Layer (Matches original API)
# ---------------------------------------------------------
transactions: List[Dict[str, Any]] = []


def add_transaction(transaction_type: str, amount: float, balance: float) -> None:
    """
    Save transaction details in memory (Legacy API).
    """
    transaction = {
        "txn_id": generate_txn_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": transaction_type,
        "amount": round(amount, 2),
        "balance": round(balance, 2)
    }
    transactions.append(transaction)


def show_transactions() -> None:
    """
    Display all transactions (Legacy API).
    """
    print("\n===== TRANSACTION HISTORY =====")
    if not transactions:
        print("No transactions found.")
        return

    for number, txn in enumerate(transactions, start=1):
        print(f"\nTransaction {number}")
        print(f"Txn ID: {txn.get('txn_id', 'N/A')}")
        print(f"Type: {txn['type']}")
        print(f"Amount: Rs. {txn['amount']:.2f}")
        print(f"Balance after transaction: Rs. {txn['balance']:.2f}")

    print("\n===============================")
