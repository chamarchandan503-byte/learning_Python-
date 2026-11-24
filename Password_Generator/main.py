"""
Password Generator - Main Application
CLI & GUI launcher for generating secure passwords.
"""

import sys

# Windows console encoding compatibility
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import password_generator


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """
    Yes/No input lene ke liye helper function.
    User seedha Enter dabaye toh default value use hoti hai.
    """
    default_str = "Y/n" if default else "y/N"
    while True:
        choice = input(f"{prompt} [{default_str}]: ").strip().lower()
        if choice == "":
            return default
        if choice in ["y", "yes", "ha", "haan"]:
            return True
        if choice in ["n", "no", "nahi"]:
            return False
        print("Kripya 'y' (haan) ya 'n' (nahi) darj karein.")


def get_password_length(min_len: int = 8, max_len: int = 128, default: int = 14) -> int:
    """
    Valid password length lene ke liye function.
    """
    while True:
        val = input(f"Password ki length darj karein ({min_len}-{max_len}) [Default {default}]: ").strip()
        if val == "":
            return default
        try:
            length = int(val)
            if length < min_len:
                print(f"Password kam se kam {min_len} characters ka hona chahiye.")
                continue
            if length > max_len:
                print(f"Maximum password length {max_len} hai.")
                continue
            return length
        except ValueError:
            print("Kripya ek valid number darj karein.")


def run_cli_generator() -> None:
    """Ek terminal-based password generation cycle chalata hai."""
    print("\n" + "=" * 45)
    print("           PASSWORD GENERATOR (CLI)")
    print("=" * 45)

    # Length input
    length = get_password_length(min_len=8, max_len=128, default=14)

    # Options input with validation
    while True:
        print("\nPassword options chuniye (Enter dabane par default 'y' select hoga):")
        use_upper = get_yes_no("1. Capital letters (A-Z) use karein?", default=True)
        use_lower = get_yes_no("2. Small letters (a-z) use karein?", default=True)
        use_digits = get_yes_no("3. Numbers (0-9) use karein?", default=True)
        use_symbols = get_yes_no("4. Special symbols (!@#$...) use karein?", default=True)

        if use_upper or use_lower or use_digits or use_symbols:
            break
        print("\n[!] Galti: Kam se kam ek option 'y' hona zaroori hai! Dobara chuniye.")

    try:
        # Password generate karein
        password = password_generator.generate_password(
            length=length,
            use_upper=use_upper,
            use_digits=use_digits,
            use_symbols=use_symbols,
            use_lower=use_lower,
        )

        strength = password_generator.check_password_strength(password)

        print("\n" + "-" * 45)
        print("[+] Aapka Generated Password:")
        print(f"\n   >>>  {password}  <<<\n")
        print(f"Length   : {len(password)} characters")
        print(f"Strength : {strength}")
        print("-" * 45)
        print("[*] Security Tip: Password ko kisi ke saath share na karein.")

    except ValueError as err:
        print(f"\n[!] Error: {err}")


def run_gui() -> None:
    """Tkinter Graphical User Interface launch karta hai."""
    try:
        import gui
        gui.main()
    except Exception as err:
        print(f"[!] GUI start karne mein samasya aayi: {err}")
        print("Terminal mode start kiya ja raha hai...\n")
        run_cli_loop()


def run_cli_loop() -> None:
    """Terminal mode loop chalata hai."""
    while True:
        run_cli_generator()
        print()
        again = get_yes_no("Kya aap ek aur password generate karna chahte hain?", default=False)
        if not again:
            print("\nShukriya! Password Generator use karne ke liye dhanyawad.\n")
            break


def main() -> None:
    # Command line arguments check karein
    if "--cli" in sys.argv:
        run_cli_loop()
        return
    if "--gui" in sys.argv:
        run_gui()
        return

    try:
        print("\n" + "=" * 45)
        print("           PASSWORD GENERATOR")
        print("=" * 45)
        print("Aap kis mode mein chalana chahte hain?")
        print("  1. Graphical Window (Desktop App) [Default]")
        print("  2. Terminal (Command-Line Mode)")
        choice = input("\nChoice darj karein (1 ya 2) [Default 1]: ").strip()

        if choice == "2":
            run_cli_loop()
        else:
            print("\nGraphical window open ho rahi hai...")
            run_gui()

    except KeyboardInterrupt:
        print("\n\nProgram band kar diya gaya. Alvida!")
        sys.exit(0)


if __name__ == "__main__":
    main()
