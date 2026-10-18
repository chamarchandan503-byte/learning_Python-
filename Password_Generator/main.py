
import password_generator


print("===== PASSWORD GENERATOR =====")

while True:
    try:
        length = int(input("Password ki length (minimum 8): "))

        if length < 8:
            print("Please enter at least 8 characters.")
            continue

        if length > 128:
            print("Maximum password length is 128.")
            continue

        break

    except ValueError:
        print("Please enter a valid number.")

use_upper = input("Capital letters use karein? (y/n): ").strip().lower() == "y"
use_digits = input("Numbers use karein? (y/n): ").strip().lower() == "y"
use_symbols = input("Symbols use karein? (y/n): ").strip().lower() == "y"

password = password_generator.generate_password(
    length,
    use_upper,
    use_digits,
    use_symbols
)

print("\nYour generated password is:")
print(password)
print("\nPassword ko kisi ke saath share na karein.")
