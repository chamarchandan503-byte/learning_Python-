
# Project 2: Calculator App

print("===== PYTHON CALCULATOR =====")

while True:
    print("\n1. Addition (+)")
    print("2. Subtraction (-)")
    print("3. Multiplication (*)")
    print("4. Division (/)")
    print("5. Exit")

    choice = input("Choose an option: ")

    if choice == "5":
        print("Calculator closed. Thank you!")
        break

    if choice not in ("1", "2", "3", "4"):
        print("Invalid choice! Try again.")
        continue

    try:
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))

        if choice == "1":
            result = num1 + num2

        elif choice == "2":
            result = num1 - num2

        elif choice == "3":
            result = num1 * num2

        elif choice == "4":
            if num2 == 0:
                print("Error: Cannot divide by zero!")
                continue
            result = num1 / num2

        print("Result:", result)

    except ValueError:
        print("Invalid input! Please enter numbers.")
