"""
Mini ATM System - Professional CLI Application.

A comprehensive, production-grade terminal-based ATM simulator featuring:
- Multi-account management with JSON data persistence
- Secure PIN authentication with brute-force retry lockout
- Cash deposits, withdrawals, and quick-cash shortcuts
- Inter-account fund transfers
- Mini-statements and printable ASCII receipts
- Robust error handling and input validation
"""

import sys
import os
import time
from datetime import datetime
from typing import Optional

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

# Enable ANSI escape sequences on Windows console
if os.name == "nt":
    os.system("")

from bank import BankSystem, BankAccount
from transaction import Transaction, format_receipt, display_mini_statement


class TerminalColors:
    """ANSI color codes for styling terminal output."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


C = TerminalColors


def clear_screen() -> None:
    """Clear terminal console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Print the professional ATM header banner."""
    curr_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    print(f"{C.CYAN}{C.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                     🏛️  APEX GLOBAL MINI ATM                     ║")
    print("║               Secure • Reliable • 24/7 Digital Banking           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{C.DIM} System Live | {curr_time} | Terminal ID: ATM-DEL-042{C.RESET}\n")


def pause_prompt(message: str = "Press [Enter] to continue...") -> None:
    """Pause execution until the user presses Enter."""
    print(f"\n{C.DIM}{message}{C.RESET}", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def prompt_float(prompt_text: str, min_val: float = 1.0) -> Optional[float]:
    """Safely prompt the user for a valid positive float number."""
    while True:
        try:
            val_str = input(prompt_text).strip()
            if not val_str:
                return None
            val = float(val_str)
            if val < min_val:
                print(f"{C.RED}Error: Amount must be at least Rs. {min_val:.2f}{C.RESET}")
                continue
            return val
        except ValueError:
            print(f"{C.RED}Error: Invalid numeric amount. Please try again.{C.RESET}")


class ATMApplication:
    """Manages ATM user session, menu interactions, and transactions."""

    def __init__(self):
        self.bank = BankSystem()
        self.current_account: Optional[BankAccount] = None
        self.last_transaction: Optional[Transaction] = None

    def prompt_receipt(self, txn: Optional[Transaction]) -> None:
        """Ask user if they would like to display or print a physical-style receipt."""
        if not txn or not self.current_account:
            return

        choice = input(f"\n{C.YELLOW}Would you like a printed receipt for this transaction? (y/N): {C.RESET}").strip().lower()
        if choice in ("y", "yes"):
            print()
            receipt_text = format_receipt(
                txn,
                self.current_account.account_number,
                self.current_account.holder_name
            )
            print(f"{C.CYAN}{receipt_text}{C.RESET}")

    def login_flow(self) -> bool:
        """
        Customer login flow supporting direct PIN or Account+PIN with 3-attempt lockout.
        """
        clear_screen()
        print_banner()
        print(f"{C.BOLD}Please authenticate to access your account.{C.RESET}")
        print(f"{C.DIM}(Demo Accounts: 1001 [PIN: 1234] | 1002 [PIN: 5678]){C.RESET}\n")

        acc_input = input("Enter Account Number (or press Enter for demo '1001'): ").strip()
        if not acc_input:
            acc_input = "1001"

        target_acc = self.bank.get_account(acc_input)
        if not target_acc:
            print(f"{C.RED}Error: Account number '{acc_input}' does not exist!{C.RESET}")
            pause_prompt()
            return False

        max_attempts = 3
        attempts_left = max_attempts

        while attempts_left > 0:
            pin = input(f"Enter 4-digit PIN for A/C {acc_input} (Attempts left: {attempts_left}): ").strip()

            if target_acc.verify_pin(pin):
                self.current_account = target_acc
                print(f"\n{C.GREEN}{C.BOLD}✔ Authentication Successful! Welcome, {target_acc.holder_name}.{C.RESET}")
                time.sleep(0.8)
                return True
            else:
                attempts_left -= 1
                if attempts_left > 0:
                    print(f"{C.RED}✘ Incorrect PIN! Please try again.{C.RESET}\n")
                else:
                    print(f"\n{C.RED}{C.BOLD}🚫 Security Alert: 3 incorrect PIN attempts! Card temporarily locked.{C.RESET}")
                    pause_prompt("Press [Enter] to exit...")
                    return False

        return False

    def check_balance(self) -> None:
        """Display account balance inquiry."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()
        print(f"{C.CYAN}{C.BOLD}═══════════════ BALANCE INQUIRY ═══════════════{C.RESET}")
        print(f" Account Number : XXXX-{self.current_account.account_number[-4:]}")
        print(f" Account Holder : {self.current_account.holder_name}")
        print(f" Ledger Balance : {C.GREEN}{C.BOLD}Rs. {self.current_account.balance:,.2f}{C.RESET}")
        print(f" Available Cash : {C.GREEN}{C.BOLD}Rs. {self.current_account.balance:,.2f}{C.RESET}")
        print(f" Daily ATM Limit: Rs. {self.current_account.daily_limit:,.2f}")
        remaining_limit = max(0.0, self.current_account.daily_limit - self.current_account.withdrawn_today)
        print(f" Today's Limit Remaining: Rs. {remaining_limit:,.2f}")
        print(f"{C.CYAN}═══════════════════════════════════════════════{C.RESET}")
        pause_prompt()

    def deposit_cash(self) -> None:
        """Handle cash deposit flow."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()
        print(f"{C.CYAN}{C.BOLD}════════════════ CASH DEPOSIT ════════════════{C.RESET}")
        print("Note: Accepted notes are Rs. 100, 200, 500.\n")

        amount = prompt_float("Enter deposit amount: Rs. ")
        if amount is None:
            print(f"{C.YELLOW}Deposit cancelled.{C.RESET}")
            pause_prompt()
            return

        success, message, txn = self.current_account.deposit(amount)
        if success:
            self.bank.save_data()
            self.last_transaction = txn
            print(f"\n{C.GREEN}{C.BOLD}✔ {message}{C.RESET}")
            print(f"Updated Balance: {C.BOLD}Rs. {self.current_account.balance:,.2f}{C.RESET}")
            self.prompt_receipt(txn)
        else:
            print(f"\n{C.RED}✘ {message}{C.RESET}")

        pause_prompt()

    def withdraw_cash(self, preset_amount: Optional[float] = None) -> None:
        """Handle cash withdrawal flow."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()
        print(f"{C.CYAN}{C.BOLD}═══════════════ CASH WITHDRAWAL ═══════════════{C.RESET}")

        if preset_amount is not None:
            amount = preset_amount
        else:
            print("Note: ATM dispenses multiples of Rs. 100 only.\n")
            amount = prompt_float("Enter withdrawal amount: Rs. ", min_val=100.0)
            if amount is None:
                print(f"{C.YELLOW}Withdrawal cancelled.{C.RESET}")
                pause_prompt()
                return

        success, message, txn = self.current_account.withdraw(amount)
        if success:
            self.bank.save_data()
            self.last_transaction = txn
            print(f"\n{C.GREEN}{C.BOLD}✔ {message}{C.RESET}")
            print(f"Remaining Balance: {C.BOLD}Rs. {self.current_account.balance:,.2f}{C.RESET}")
            self.prompt_receipt(txn)
        else:
            print(f"\n{C.RED}✘ {message}{C.RESET}")

        pause_prompt()

    def quick_cash_menu(self) -> None:
        """Display Quick Cash preset buttons."""
        clear_screen()
        print_banner()
        print(f"{C.CYAN}{C.BOLD}═════════════════ QUICK CASH ═════════════════{C.RESET}")
        print("  1. Rs. 500          2. Rs. 1,000")
        print("  3. Rs. 2,000        4. Rs. 5,000")
        print("  5. Rs. 10,000       6. Back to Main Menu")
        print(f"{C.CYAN}──────────────────────────────────────────────{C.RESET}")

        choice = input("Select Quick Cash option [1-6]: ").strip()
        preset_map = {
            "1": 500.0,
            "2": 1000.0,
            "3": 2000.0,
            "4": 5000.0,
            "5": 10000.0
        }

        if choice in preset_map:
            self.withdraw_cash(preset_amount=preset_map[choice])
        elif choice == "6":
            return
        else:
            print(f"{C.RED}Invalid option selected.{C.RESET}")
            pause_prompt()

    def transfer_funds(self) -> None:
        """Handle inter-account fund transfer."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()
        print(f"{C.CYAN}{C.BOLD}════════════════ FUND TRANSFER ════════════════{C.RESET}")
        print("Transfer money instantly to another bank account.\n")

        dest_acc_num = input("Enter Recipient Account Number (e.g., 1002): ").strip()
        if not dest_acc_num:
            print(f"{C.YELLOW}Transfer cancelled.{C.RESET}")
            pause_prompt()
            return

        target_acc = self.bank.get_account(dest_acc_num)
        if not target_acc:
            print(f"{C.RED}Error: Beneficiary account '{dest_acc_num}' not found!{C.RESET}")
            pause_prompt()
            return

        if target_acc.account_number == self.current_account.account_number:
            print(f"{C.RED}Error: You cannot transfer funds to your own account.{C.RESET}")
            pause_prompt()
            return

        print(f"Beneficiary Name: {C.BOLD}{target_acc.holder_name}{C.RESET}")
        amount = prompt_float("Enter transfer amount: Rs. ")
        if amount is None:
            print(f"{C.YELLOW}Transfer cancelled.{C.RESET}")
            pause_prompt()
            return

        confirm = input(
            f"\nConfirm transfer of Rs. {amount:.2f} to {target_acc.holder_name} (A/C: {target_acc.account_number})? (y/N): "
        ).strip().lower()

        if confirm not in ("y", "yes"):
            print(f"{C.YELLOW}Transfer cancelled by user.{C.RESET}")
            pause_prompt()
            return

        success, message, tx_tuple = self.current_account.transfer_to(target_acc, amount)
        if success and tx_tuple:
            self.bank.save_data()
            self.last_transaction = tx_tuple[0]  # Sender transaction
            print(f"\n{C.GREEN}{C.BOLD}✔ {message}{C.RESET}")
            print(f"Your Remaining Balance: {C.BOLD}Rs. {self.current_account.balance:,.2f}{C.RESET}")
            self.prompt_receipt(self.last_transaction)
        else:
            print(f"\n{C.RED}✘ {message}{C.RESET}")

        pause_prompt()

    def mini_statement(self) -> None:
        """Display mini statement of recent transactions."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()
        statement = display_mini_statement(
            self.current_account.transactions,
            self.current_account.account_number,
            self.current_account.holder_name,
            limit=5
        )
        print(f"{C.CYAN}{statement}{C.RESET}")
        pause_prompt()

    def print_last_receipt(self) -> None:
        """Display the receipt of the most recent transaction."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()

        txn_to_print = self.last_transaction
        if not txn_to_print and self.current_account.transactions:
            txn_to_print = self.current_account.transactions[-1]

        if not txn_to_print:
            print(f"{C.YELLOW}No recent transactions available to print receipt.{C.RESET}")
        else:
            receipt = format_receipt(
                txn_to_print,
                self.current_account.account_number,
                self.current_account.holder_name
            )
            print(f"{C.CYAN}{receipt}{C.RESET}")

        pause_prompt()

    def change_pin(self) -> None:
        """Handle PIN change workflow."""
        if not self.current_account:
            return

        clear_screen()
        print_banner()
        print(f"{C.CYAN}{C.BOLD}════════════════ PIN CHANGE ════════════════{C.RESET}")

        old_pin = input("Enter current 4-digit PIN: ").strip()
        new_pin = input("Enter new 4-digit PIN: ").strip()
        confirm_pin = input("Re-enter new 4-digit PIN to confirm: ").strip()

        if new_pin != confirm_pin:
            print(f"\n{C.RED}Error: New PIN and Confirmation PIN do not match!{C.RESET}")
            pause_prompt()
            return

        success, message = self.current_account.change_pin(old_pin, new_pin)
        if success:
            self.bank.save_data()
            print(f"\n{C.GREEN}{C.BOLD}✔ {message}{C.RESET}")
        else:
            print(f"\n{C.RED}✘ {message}{C.RESET}")

        pause_prompt()

    def run_menu(self) -> None:
        """Main ATM operation menu loop."""
        while True:
            clear_screen()
            print_banner()
            if not self.current_account:
                break

            masked_acc = f"XXXX-{self.current_account.account_number[-4:]}"
            print(f" Customer: {C.BOLD}{self.current_account.holder_name}{C.RESET} | A/C: {masked_acc}")
            print("┌──────────────────────────────────────────────────────────────┐")
            print("│                     ATM SERVICE MENU                         │")
            print("├──────────────────────────────┬───────────────────────────────┤")
            print("│  [1] 💰 Check Balance        │  [5] 🔄 Fund Transfer         │")
            print("│  [2] 💵 Deposit Cash         │  [6] 📜 Mini Statement        │")
            print("│  [3] 🏧 Withdraw Cash        │  [7] 🧾 Print Last Receipt    │")
            print("│  [4] ⚡ Quick Cash           │  [8] 🔑 Change ATM PIN        │")
            print("├──────────────────────────────┴───────────────────────────────┤")
            print("│  [9] 🚪 Logout & Eject Card                                  │")
            print("└──────────────────────────────────────────────────────────────┘")

            choice = input(f"\n{C.BOLD}Enter option [1-9]: {C.RESET}").strip()

            if choice == "1":
                self.check_balance()
            elif choice == "2":
                self.deposit_cash()
            elif choice == "3":
                self.withdraw_cash()
            elif choice == "4":
                self.quick_cash_menu()
            elif choice == "5":
                self.transfer_funds()
            elif choice == "6":
                self.mini_statement()
            elif choice == "7":
                self.print_last_receipt()
            elif choice == "8":
                self.change_pin()
            elif choice == "9":
                clear_screen()
                print_banner()
                print(f"{C.GREEN}{C.BOLD}✔ Please remove your card.{C.RESET}")
                print(f"{C.CYAN}Thank you for choosing APEX Global Bank! Have a nice day! 👋{C.RESET}\n")
                time.sleep(1.2)
                break
            else:
                print(f"{C.RED}Invalid option '{choice}'. Please select a valid number from 1 to 9.{C.RESET}")
                time.sleep(1.0)


def main():
    """Application entry point."""
    app = ATMApplication()
    try:
        while True:
            if not app.login_flow():
                # If authentication failed or cancelled, exit program
                break

            app.run_menu()

            # Ask if another user wants to use the ATM
            clear_screen()
            print_banner()
            another = input("Would another customer like to log in? (y/N): ").strip().lower()
            if another not in ("y", "yes"):
                print(f"\n{C.GREEN}ATM session ended. Goodbye!{C.RESET}\n")
                break

    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}Session cancelled by user (Ctrl+C). Card safely ejected. Goodbye!{C.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
