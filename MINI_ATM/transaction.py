
# transactions.py
# Mini ATM Transaction History

transactions = []


def add_transaction(transaction_type, amount, balance):
    """Save transaction details in memory."""

    transaction = {
        "type": transaction_type,
        "amount": amount,
        "balance": balance
    }

    transactions.append(transaction)


def show_transactions():
    """Display all transactions."""

    print("\n===== TRANSACTION HISTORY =====")

    if not transactions:
        print("No transactions found.")
        return

    for number, transaction in enumerate(transactions, start=1):
        print(f"\nTransaction {number}")
        print(f"Type: {transaction['type']}")
        print(f"Amount: Rs. {transaction['amount']:.2f}")
        print(f"Balance after transaction: "
              f"Rs. {transaction['balance']:.2f}")

    print("\n===============================")
