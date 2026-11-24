"""
Password Generator Module
Secure and customizable password generation using Python's secrets module.
"""

import secrets
import string


def generate_password(
    length: int = 12,
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    use_lower: bool = True,
) -> str:
    """
    Ek cryptographically secure random password generate karta hai.

    Args:
        length (int): Password ki total length (minimum 8 characters). Default: 12.
        use_upper (bool): Uppercase letters (A-Z) include karein. Default: True.
        use_digits (bool): Digits (0-9) include karein. Default: True.
        use_symbols (bool): Special symbols (!@#$%^&*...) include karein. Default: True.
        use_lower (bool): Lowercase letters (a-z) include karein. Default: True.

    Returns:
        str: Generated secure password.

    Raises:
        ValueError: Agar length 8 se kam ho ya koi bhi character type select na ho.
    """
    if length < 8:
        raise ValueError("Password ki length kam se kam 8 characters honi chahiye.")

    character_pool = ""
    guaranteed_chars = []
    rng = secrets.SystemRandom()

    # User ke selection ke hisaab se pool aur guaranteed characters banayein
    if use_lower:
        character_pool += string.ascii_lowercase
        guaranteed_chars.append(rng.choice(string.ascii_lowercase))

    if use_upper:
        character_pool += string.ascii_uppercase
        guaranteed_chars.append(rng.choice(string.ascii_uppercase))

    if use_digits:
        character_pool += string.digits
        guaranteed_chars.append(rng.choice(string.digits))

    if use_symbols:
        symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        character_pool += symbols
        guaranteed_chars.append(rng.choice(symbols))

    # Kam se kam ek character type hona zaroori hai
    if not character_pool:
        raise ValueError(
            "Kam se kam ek character type (uppercase, lowercase, numbers, ya symbols) chunna zaroori hai."
        )

    if length < len(guaranteed_chars):
        raise ValueError(
            f"Chuni gayi options ke mutabiq length kam se kam {len(guaranteed_chars)} honi chahiye."
        )

    # Remaining length ke characters select karein
    remaining_length = length - len(guaranteed_chars)
    password_chars = guaranteed_chars + [
        rng.choice(character_pool) for _ in range(remaining_length)
    ]

    # Predictable pattern avoid karne ke liye shuffle karein
    rng.shuffle(password_chars)

    return "".join(password_chars)


def check_password_strength(password: str) -> str:
    """
    Password ki strength evaluate karta hai.

    Returns:
        str: 'Weak', 'Medium', 'Strong', ya 'Very Strong'
    """
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1
    if has_lower and has_upper:
        score += 1
    if has_digit:
        score += 1
    if has_symbol:
        score += 1

    if score <= 2:
        return "Weak (Kamzor)"
    elif score <= 4:
        return "Medium (Theek-thaak)"
    elif score <= 5:
        return "Strong (Mazboot)"
    else:
        return "Very Strong (Bahut Mazboot)"


def check_password_strength(password: str) -> str:
    """
    Password ki strength evaluate karta hai.

    Returns:
        str: 'Weak', 'Medium', 'Strong', ya 'Very Strong'
    """
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1
    if has_lower and has_upper:
        score += 1
    if has_digit:
        score += 1
    if has_symbol:
        score += 1

    if score <= 2:
        return "Weak (Kamzor)"
    elif score <= 4:
        return "Medium (Theek-thaak)"
    elif score <= 5:
        return "Strong (Mazboot)"
    else:
        return "Very Strong (Bahut Mazboot)"

