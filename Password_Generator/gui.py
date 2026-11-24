"""
Password Generator - Graphical User Interface (GUI)
Tkinter-based desktop application for generating secure passwords.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import password_generator


class PasswordGeneratorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Password Generator")
        self.root.geometry("500x580")
        self.root.resizable(False, False)
        self.root.configure(bg="#f3f4f6")

        # Center window on screen
        self.center_window(500, 580)

        # Variables
        self.length_var = tk.IntVar(value=14)
        self.use_upper_var = tk.BooleanVar(value=True)
        self.use_lower_var = tk.BooleanVar(value=True)
        self.use_digits_var = tk.BooleanVar(value=True)
        self.use_symbols_var = tk.BooleanVar(value=True)
        self.password_var = tk.StringVar(value="")
        self.strength_var = tk.StringVar(value="")

        self.setup_ui()
        self.generate()

    def center_window(self, width: int, height: int) -> None:
        """Window ko screen ke center me position karta hai."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self) -> None:
        """UI widgets layout create karta hai."""
        # Top Header Frame
        header_frame = tk.Frame(self.root, bg="#1e293b", pady=16)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="🔐 Password Generator",
            font=("Segoe UI", 18, "bold"),
            bg="#1e293b",
            fg="#ffffff",
        )
        title_lbl.pack()

        subtitle_lbl = tk.Label(
            header_frame,
            text="Generate strong, cryptographically secure passwords",
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#94a3b8",
        )
        subtitle_lbl.pack(pady=(4, 0))

        # Main Container
        container = tk.Frame(self.root, bg="#f3f4f6", padx=20, pady=16)
        container.pack(fill="both", expand=True)

        # Password Result Card
        result_card = tk.Frame(container, bg="#ffffff", bd=1, relief="solid", padx=12, pady=12)
        result_card.configure(highlightbackground="#e2e8f0", highlightthickness=1)
        result_card.pack(fill="x", pady=(0, 14))

        pw_display_frame = tk.Frame(result_card, bg="#ffffff")
        pw_display_frame.pack(fill="x")

        self.pw_entry = tk.Entry(
            pw_display_frame,
            textvariable=self.password_var,
            font=("Consolas", 14, "bold"),
            bg="#f8fafc",
            fg="#0f172a",
            relief="flat",
            bd=6,
            justify="center",
            state="readonly",
        )
        self.pw_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.copy_btn = tk.Button(
            pw_display_frame,
            text="📋 Copy",
            font=("Segoe UI", 10, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.copy_to_clipboard,
        )
        self.copy_btn.pack(side="right")

        # Strength Indicator
        self.strength_lbl = tk.Label(
            result_card,
            textvariable=self.strength_var,
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#16a34a",
        )
        self.strength_lbl.pack(anchor="w", pady=(8, 0))

        # Settings Card
        settings_card = tk.LabelFrame(
            container,
            text=" Password Settings ",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=14,
            pady=12,
        )
        settings_card.pack(fill="x", pady=(0, 14))

        # Length Slider
        length_top_frame = tk.Frame(settings_card, bg="#ffffff")
        length_top_frame.pack(fill="x", pady=(0, 4))

        tk.Label(
            length_top_frame,
            text="Password Length:",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#334155",
        ).pack(side="left")

        self.length_display = tk.Label(
            length_top_frame,
            text=f"{self.length_var.get()} characters",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#0284c7",
        )
        self.length_display.pack(side="right")

        length_scale = ttk.Scale(
            settings_card,
            from_=8,
            to=64,
            variable=self.length_var,
            orient="horizontal",
            command=self.on_length_change,
        )
        length_scale.pack(fill="x", pady=(0, 10))

        # Checkboxes for character types
        tk.Label(
            settings_card,
            text="Include Characters:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#334155",
        ).pack(anchor="w", pady=(4, 6))

        options = [
            ("Uppercase Letters (A-Z)", self.use_upper_var),
            ("Lowercase Letters (a-z)", self.use_lower_var),
            ("Numbers (0-9)", self.use_digits_var),
            ("Special Symbols (!@#$%...)", self.use_symbols_var),
        ]

        for text, var in options:
            cb = tk.Checkbutton(
                settings_card,
                text=text,
                variable=var,
                font=("Segoe UI", 10),
                bg="#ffffff",
                fg="#1e293b",
                activebackground="#ffffff",
                selectcolor="#ffffff",
                cursor="hand2",
                command=self.validate_options,
            )
            cb.pack(anchor="w", pady=2)

        # Generate Button
        self.gen_btn = tk.Button(
            container,
            text="⚡ Generate Password",
            font=("Segoe UI", 12, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=self.generate,
        )
        self.gen_btn.pack(fill="x", pady=(0, 10))

        # Footer Info
        footer = tk.Label(
            container,
            text="🔒 Generated passwords are secure and never saved anywhere.",
            font=("Segoe UI", 8),
            bg="#f3f4f6",
            fg="#64748b",
        )
        footer.pack()

    def on_length_change(self, val: str) -> None:
        """Slider change hone par label update karta hai."""
        rounded = int(float(val))
        self.length_var.set(rounded)
        self.length_display.config(text=f"{rounded} characters")

    def validate_options(self) -> None:
        """Kam se kam ek option check hona chahiye."""
        if not any([
            self.use_upper_var.get(),
            self.use_lower_var.get(),
            self.use_digits_var.get(),
            self.use_symbols_var.get(),
        ]):
            messagebox.showwarning(
                "Option Required",
                "Kam se kam ek character type (Uppercase, Lowercase, Numbers ya Symbols) select hona zaroori hai!"
            )
            self.use_lower_var.set(True)

    def generate(self) -> None:
        """Naya password generate karta hai aur screen par dikhata hai."""
        length = self.length_var.get()
        use_upper = self.use_upper_var.get()
        use_lower = self.use_lower_var.get()
        use_digits = self.use_digits_var.get()
        use_symbols = self.use_symbols_var.get()

        if not (use_upper or use_lower or use_digits or use_symbols):
            self.validate_options()
            return

        try:
            pw = password_generator.generate_password(
                length=length,
                use_upper=use_upper,
                use_digits=use_digits,
                use_symbols=use_symbols,
                use_lower=use_lower,
            )
            self.password_var.set(pw)

            # Strength update
            strength = password_generator.check_password_strength(pw)
            self.update_strength_display(strength)

            # Reset copy button text
            self.copy_btn.config(text="📋 Copy", bg="#0284c7")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_strength_display(self, strength: str) -> None:
        """Strength ke hisaab se color aur text update karta hai."""
        self.strength_var.set(f"Strength: {strength}")
        if "Weak" in strength:
            self.strength_lbl.config(fg="#dc2626")
        elif "Medium" in strength:
            self.strength_lbl.config(fg="#d97706")
        elif "Very Strong" in strength:
            self.strength_lbl.config(fg="#15803d")
        else:
            self.strength_lbl.config(fg="#16a34a")

    def copy_to_clipboard(self) -> None:
        """Password ko clipboard me copy karta hai."""
        pw = self.password_var.get()
        if pw:
            self.root.clipboard_clear()
            self.root.clipboard_append(pw)
            self.copy_btn.config(text="✓ Copied!", bg="#16a34a")
            self.root.after(2000, lambda: self.copy_btn.config(text="📋 Copy", bg="#0284c7"))


def main() -> None:
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
