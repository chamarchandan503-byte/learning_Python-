
# bank.py
# Banking Functions for Mini ATM

balance = 5000.0


def check_balance():
    """Display current bank balance."""
    print(f"Your Current Balance: Rs. {balance:.2f}")


def deposit_money(amount):
    """Deposit money into the account."""
    global balance

    if amount <= 0:
        print("Error: Amount must be greater than zero.")
        return False

    balance += amount
    print(f"Rs. {amount:.2f} deposited successfully!")
    print(f"New Balance: Rs. {balance:.2f}")
    return True


def withdraw_money(amount):
    """Withdraw money from the account."""
    global balance

    if amount <= 0:
        print("Error: Amount must be greater than zero.")
        return False

    if amount > balance:
        print("Error: Insufficient balance!")
        return False

    balance -= amount
    print(f"Please collect Rs. {amount:.2f}")
    print(f"Remaining Balance: Rs. {balance:.2f}")
    return True
