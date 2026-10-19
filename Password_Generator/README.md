# Password Generator in Python

## Project Description
Password Generator is a simple Python project that generates random and strong passwords. Users can choose the password length and decide whether to include uppercase letters, numbers, and symbols.

## Features
- Generate random passwords.
- Choose password length from 8 to 128 characters.
- Include uppercase letters.
- Include numbers.
- Include special symbols.
- Use Python's secure `secrets` module.
- Validate user input.

## Technologies Used
- Python
- `secrets` module
- `string` module
- VS Code

## Project Structure
```text
Project_05_Password_Generator/
│
├── main.py
├── password_generator.py
└── README.md
```

## Requirements
- Python 3 installed on your computer.
- Visual Studio Code (recommended).

No external libraries are required.

## How to Run
1. Download or clone the project.
2. Open the project folder in VS Code.
3. Open the terminal.
4. Run the following command:

```bash
python main.py
```

5. Enter the desired password length.
6. Choose whether to include uppercase letters, numbers, and symbols.
7. Copy the generated password and store it securely.

## Example Output
```text
===== PASSWORD GENERATOR =====
Password ki length (minimum 8): 12
Capital letters use karein? (y/n): y
Numbers use karein? (y/n): y
Symbols use karein? (y/n): y

Your generated password is:
[Generated password]
```

The actual password will be different each time.

## Learning Objectives
- Understand Python functions.
- Learn how to use modules.
- Work with strings and character sets.
- Use conditional statements and loops.
- Handle invalid user input.
- Learn basic secure password generation.

## Future Improvements
- Add a graphical user interface (GUI).
- Add a copy-to-clipboard feature.
- Add password strength information.
- Allow users to save passwords securely.

## Security Note
This project generates passwords but does not store or manage them. Never upload real passwords, API keys