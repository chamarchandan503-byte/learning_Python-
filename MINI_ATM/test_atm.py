"""
Comprehensive Unit Tests for Mini ATM System.

Validates core banking operations:
- Deposits, withdrawals, and balance updates
- Overdraw prevention and daily limits
- Inter-account fund transfers
- PIN authentication and PIN change validations
- Mini-statement and receipt generation
"""

import unittest
from bank import BankAccount, BankSystem
from transaction import Transaction, format_receipt, display_mini_statement


class TestATMSystem(unittest.TestCase):
    """Unit test suite for ATM business logic."""

    def setUp(self):
        """Set up fresh isolated test accounts."""
        self.account_a = BankAccount(
            account_number="9001",
            holder_name="Test User A",
            pin="1234",
            balance=10000.0,
            daily_limit=20000.0
        )
        self.account_b = BankAccount(
            account_number="9002",
            holder_name="Test User B",
            pin="4321",
            balance=5000.0,
            daily_limit=20000.0
        )

    def test_pin_verification(self):
        """Test PIN matching and rejection."""
        self.assertTrue(self.account_a.verify_pin("1234"))
        self.assertFalse(self.account_a.verify_pin("0000"))
        self.assertFalse(self.account_a.verify_pin(""))

    def test_deposit(self):
        """Test valid and invalid deposit amounts."""
        # Valid deposit
        success, msg, txn = self.account_a.deposit(2000.0)
        self.assertTrue(success)
        self.assertEqual(self.account_a.balance, 12000.0)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 2000.0)
        self.assertEqual(txn.balance_after, 12000.0)

        # Zero or negative deposit
        fail_success, fail_msg, _ = self.account_a.deposit(0)
        self.assertFalse(fail_success)

        fail_neg, _, _ = self.account_a.deposit(-500)
        self.assertFalse(fail_neg)

    def test_withdrawal(self):
        """Test cash withdrawal rules, multiples of 100, and limits."""
        # Valid withdrawal
        success, msg, txn = self.account_a.withdraw(1500.0)
        self.assertTrue(success)
        self.assertEqual(self.account_a.balance, 8500.0)
        self.assertEqual(self.account_a.withdrawn_today, 1500.0)

        # Non-multiple of 100
        fail_mod, _, _ = self.account_a.withdraw(250.0)
        self.assertFalse(fail_mod)

        # Exceeding balance
        fail_bal, _, _ = self.account_a.withdraw(50000.0)
        self.assertFalse(fail_bal)

    def test_transfer_between_accounts(self):
        """Test peer-to-peer account fund transfers."""
        initial_bal_a = self.account_a.balance
        initial_bal_b = self.account_b.balance
        transfer_amt = 3000.0

        success, msg, tx_pair = self.account_a.transfer_to(self.account_b, transfer_amt)
        self.assertTrue(success)
        self.assertEqual(self.account_a.balance, initial_bal_a - transfer_amt)
        self.assertEqual(self.account_b.balance, initial_bal_b + transfer_amt)
        self.assertIsNotNone(tx_pair)
        debit_tx, credit_tx = tx_pair
        self.assertEqual(debit_tx.type, "TRANSFER_SENT")
        self.assertEqual(credit_tx.type, "TRANSFER_RECEIVED")

    def test_change_pin(self):
        """Test PIN change security rules."""
        # Wrong old pin
        ok, _ = self.account_a.change_pin("9999", "5678")
        self.assertFalse(ok)

        # Invalid format (non-digit or wrong length)
        ok, _ = self.account_a.change_pin("1234", "12a4")
        self.assertFalse(ok)

        ok, _ = self.account_a.change_pin("1234", "123")
        self.assertFalse(ok)

        # Identical PIN
        ok, _ = self.account_a.change_pin("1234", "1234")
        self.assertFalse(ok)

        # Valid PIN change
        ok, msg = self.account_a.change_pin("1234", "9876")
        self.assertTrue(ok)
        self.assertTrue(self.account_a.verify_pin("9876"))

    def test_receipt_and_statement_formatting(self):
        """Test receipt and statement generation without errors."""
        self.account_a.deposit(500.0)
        last_txn = self.account_a.transactions[-1]
        receipt = format_receipt(last_txn, self.account_a.account_number, self.account_a.holder_name)
        self.assertIn("TRANSACTION RECEIPT", receipt)
        self.assertIn("XXXX-9001", receipt)

        statement = display_mini_statement(
            self.account_a.transactions,
            self.account_a.account_number,
            self.account_a.holder_name
        )
        self.assertIn("MINI STATEMENT", statement)


if __name__ == "__main__":
    unittest.main()
