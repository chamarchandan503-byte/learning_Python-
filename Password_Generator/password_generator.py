
import secrets
import string


def generate_password(length, use_upper, use_digits, use_symbols):
    if length < 8:
        raise ValueError("Password length must be at least 8.")

    characters = string.ascii_lowercase
    required_characters = [secrets.choice(string.ascii_lowercase)]

    if use_upper:
        characters += string.ascii_uppercase
        required_characters.append(
            secrets.choice(string.ascii_uppercase)
        )

    if use_digits:
        characters += string.digits
        required_characters.append(secrets.choice(string.digits))

    if use_symbols:
        symbols = "!@#$%^&*()-_=+?"
        characters += symbols
        required_characters.append(secrets.choice(symbols))

    remaining_length = length - len(required_characters)

    password_characters = required_characters + [
        secrets.choice(characters)
        for _ in range(remaining_length)
    ]

    # Password characters ko random order mein arrange karein
    secrets.SystemRandom().shuffle(password_characters)

    return "".join(password_characters)
