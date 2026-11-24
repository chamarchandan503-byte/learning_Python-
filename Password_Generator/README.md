# Password Generator in Python

## Project Description
Password Generator is a clean, secure, and user-friendly Python project that generates strong, random passwords. It includes both a **modern Desktop GUI application** (with window, buttons, slider, and clipboard copy) and an interactive **Command-Line Interface (CLI)**.

## Features
- **Modern Desktop GUI**:
  - Clean card-based visual interface using Tkinter.
  - Interactive password length slider (8 to 64 characters).
  - Checkboxes for uppercase, lowercase, numbers, and symbols.
  - One-click **Copy to Clipboard** button.
  - Real-time password strength meter.
  - Auto-centers window on launch.
- **Cryptographically Secure**: Uses Python's built-in `secrets` module instead of `random`.
- **Customizable Length**: Choose password length from 8 to 128 characters (default: 14).
- **Guaranteed Inclusion**: Ensures at least one character from each selected character set is included.
- **Password Strength Analyzer**: Displays whether the generated password is Weak, Medium, Strong, or Very Strong.
- **Input Validation**: Gracefully handles invalid inputs and prevents empty character pools.

## Project Structure
```text
Password_Generator/
│
├── gui.py                  # Graphical desktop application (Tkinter)
├── main.py                 # Main launcher (allows selecting GUI or Terminal)
├── password_generator.py   # Core logic for password generation & strength check
└── README.md               # Documentation
```

## How to Run

### Method 1: Graphical Desktop App (Recommended)
Open your terminal in the `Password_Generator` folder and run:
```bash
python gui.py
```
*Ya fir VS Code me [gui.py](gui.py) open karke top-right corner par **Play (▶️)** button dabayein.*

Ek sundar window khul jayegi jahan aap:
1. Slider se length adjust kar sakte hain.
2. Character options check/uncheck kar sakte hain.
3. **"Generate Password"** button par click karke turant naya password bana sakte hain.
4. **"Copy"** button dabakar password copy kar sakte hain.

---

### Method 2: Main Launcher
```bash
python main.py
```
Isme aapse poocha jayega ki aap **Graphical Window** chalana chahte hain ya **Terminal Mode**. Seedha **Enter** dabane par GUI window khul jayegi!

---

### Method 3: Direct Terminal CLI Mode
Agar terminal me text ke roop me password generate karna ho:
```bash
python main.py --cli
```

## Security Note
This project generates passwords locally on your machine and never stores, logs, or transmits them. Never share your real passwords, API keys, or private credentials with anyone or commit them to public repositories.
