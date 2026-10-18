# Mini ATM System
# Project 01

balance = 5000
correct_pin = "1234"
transactions = []

print("=" * 30)
print("       WELCOME TO ATM")
print("=" * 30)

pin = input("Enter your 4-digit PIN: ")

if pin != correct_pin:
    print("Incorrect PIN! Access Denied.")

else:
    print("\nLogin Successful!")

    while True:
        print("\n------ ATM MENU ------")
        print("1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Transaction History")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            print(f"Your Balance: Rs. {balance}")

        elif choice == "2":
            try:
                amount = float(input("Enter deposit amount: Rs. "))

                if amount <= 0:
                    print("Amount must be greater than zero.")

                else:
                    balance += amount
                    transactions.append(
                        f"Deposited Rs. {amount:.2f}"
                    )
                    print("Money deposited successfully!")
                    print(f"New Balance: Rs. {balance:.2f}")

            except ValueError:
                print("Please enter a valid number.")

        elif choice == "3":
            try:
                amount = float(input("Enter withdrawal amount: Rs. "))

                if amount <= 0:
                    print("Amount must be greater than zero.")

                elif amount > balance:
                    print("Insufficient Balance!")

                else:
                    balance -= amount
                    transactions.append(
                        f"Withdrawn Rs. {amount:.2f}"
                    )
                    print("Please collect your money.")
                    print(f"Remaining Balance: Rs. {balance:.2f}")

            except ValueError:
                print("Please enter a valid number.")

        elif choice == "4":
            print("\n--- Transaction History ---")

            if not transactions:
                print("No transactions yet.")

            else:
                for transaction in transactions:
                    print(transaction)

        elif choice == "5":
            print("Thank you for using our ATM!")
            break

        else:
            print("Invalid choice! Please try again.")