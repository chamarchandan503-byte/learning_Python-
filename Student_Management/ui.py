"""
ui.py - Terminal User Interface & Visual Report Generator.

Provides ANSI color formatting, responsive Unicode tables,
visual academic transcripts, bar charts, and robust input prompts.
"""

from __future__ import annotations
import os
import sys
from typing import List, Dict, Any, Optional

# Enable ANSI escape sequences on Windows consoles
if os.name == "nt":
    os.system("")

# Configure UTF-8 on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class Colors:
    """Terminal ANSI colors and styling."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Background
    BG_BLUE = "\033[44m"
    BG_CYAN = "\033[46m"
    BG_GREEN = "\033[42m"
    BG_DARK = "\033[100m"


C = Colors


def clear_screen() -> None:
    """Clear terminal console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Display the application header banner."""
    print(f"{C.CYAN}{C.BOLD}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║             STUDENT MANAGEMENT & ACADEMIC INFORMATION SYSTEM               ║")
    print("║               Enterprise Academic Records & Analytics Platform             ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")


def print_section_header(title: str, icon: str = "📌") -> None:
    """Display a distinct section sub-header."""
    print(f"\n{C.YELLOW}{C.BOLD}{icon}  {title.upper()}{C.RESET}")
    print(f"{C.DIM}{'─' * (len(title) + 6)}{C.RESET}")


def print_success(message: str) -> None:
    """Print a success confirmation message."""
    print(f"{C.GREEN}{C.BOLD}✔  {message}{C.RESET}")


def print_error(message: str) -> None:
    """Print an error alert."""
    print(f"{C.RED}{C.BOLD}✖  Error: {message}{C.RESET}")


def print_warning(message: str) -> None:
    """Print a warning notification."""
    print(f"{C.YELLOW}{C.BOLD}⚠  Warning: {message}{C.RESET}")


def print_info(message: str) -> None:
    """Print an informational remark."""
    print(f"{C.CYAN}ℹ  {message}{C.RESET}")


def pause() -> None:
    """Wait for user to press Enter before returning."""
    print(f"\n{C.DIM}Press [Enter] to continue...{C.RESET}", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def draw_table(
    headers: List[str],
    rows: List[List[Any]],
    alignments: Optional[List[str]] = None,
    title: Optional[str] = None
) -> None:
    """
    Draw a clean, Unicode-bordered data table with dynamic column sizing.
    alignments: list of 'L' (left), 'R' (right), 'C' (center).
    """
    if not headers:
        return

    col_count = len(headers)
    if not alignments:
        alignments = ["L"] * col_count

    # Determine maximum width for each column
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for idx in range(min(col_count, len(row))):
            val_str = str(row[idx])
            if len(val_str) > col_widths[idx]:
                col_widths[idx] = len(val_str)

    # Pad widths
    col_widths = [w + 2 for w in col_widths]
    total_table_width = sum(col_widths) + (col_count - 1) + 2

    # Draw Title if provided
    if title:
        print(f"\n{C.CYAN}{C.BOLD}┌─ {title} " + "─" * max(0, total_table_width - len(title) - 5) + f"┐{C.RESET}")

    # Top border
    top_line = "┌" + "┬".join("─" * w for w in col_widths) + "┐"
    mid_line = "├" + "┼".join("─" * w for w in col_widths) + "┤"
    bot_line = "└" + "┴".join("─" * w for w in col_widths) + "┘"

    print(f"{C.DIM}{top_line}{C.RESET}")

    # Header Row
    header_cells = []
    for h, w, a in zip(headers, col_widths, alignments):
        if a == "R":
            header_cells.append(f" {str(h):>{w-2}} ")
        elif a == "C":
            header_cells.append(f" {str(h):^{w-2}} ")
        else:
            header_cells.append(f" {str(h):<{w-2}} ")

    print(f"{C.BOLD}│" + "│".join(f"{C.CYAN}{c}{C.RESET}{C.BOLD}" for c in header_cells) + f"│{C.RESET}")
    print(f"{C.DIM}{mid_line}{C.RESET}")

    # Data Rows
    if not rows:
        empty_msg = "No records found"
        print(f"│ {empty_msg:^{total_table_width - 4}} │")
    else:
        for row in rows:
            row_cells = []
            for idx in range(col_count):
                val = str(row[idx]) if idx < len(row) else ""
                w = col_widths[idx]
                a = alignments[idx] if idx < len(alignments) else "L"

                if a == "R":
                    cell = f" {val:>{w-2}} "
                elif a == "C":
                    cell = f" {val:^{w-2}} "
                else:
                    cell = f" {val:<{w-2}} "
                row_cells.append(cell)

            print("│" + "│".join(row_cells) + "│")

    print(f"{C.DIM}{bot_line}{C.RESET}")


def render_progress_bar(percentage: float, length: int = 20) -> str:
    """Render an ASCII visual progress bar for percentages."""
    clamped = max(0.0, min(100.0, percentage))
    filled_len = int(round((clamped / 100.0) * length))
    bar = "█" * filled_len + "░" * (length - filled_len)

    if clamped >= 75.0:
        color = C.GREEN
    elif clamped >= 50.0:
        color = C.YELLOW
    else:
        color = C.RED

    return f"{color}[{bar}] {clamped:5.1f}%{C.RESET}"


def display_report_card(student: Any) -> None:
    """
    Generate and render a complete official Academic Marksheet & Transcript.
    """
    clear_screen()
    w = 78

    print(f"{C.CYAN}{C.BOLD}╔" + "═" * (w - 2) + "╗")
    print(f"║{'OFFICIAL ACADEMIC TRANSCRIPT & PERFORMANCE REPORT':^{w-2}}║")
    print(f"║{'GOVERNMENT ENGINEERING & TECHNOLOGY INSTITUTE':^{w-2}}║")
    print("╠" + "═" * (w - 2) + "╣" + f"{C.RESET}")

    # Student Info Grid
    print(f"  {C.BOLD}Student Name :{C.RESET} {student.name:<25} {C.BOLD}Roll Number :{C.RESET} {student.roll_number}")
    print(f"  {C.BOLD}Course / Dept:{C.RESET} {student.course:<25} {C.BOLD}Semester    :{C.RESET} Sem-{student.semester}")
    print(f"  {C.BOLD}Email Contact:{C.RESET} {student.email or 'N/A':<25} {C.BOLD}Contact No  :{C.RESET} {student.phone or 'N/A'}")
    print(f"  {C.BOLD}Enroll Status:{C.RESET} {student.status:<25} {C.BOLD}Academic Yr :{C.RESET} 2026-2027")
    print(f"{C.DIM}  " + "─" * (w - 4) + f"{C.RESET}")

    # Subject Performance Table
    sub_headers = ["#", "Subject Name", "Max", "Obtained", "Grade", "Status"]
    sub_rows = []
    idx = 1
    for sub in student.subjects.values():
        status_label = f"{C.GREEN}PASS{C.RESET}" if sub.is_pass else f"{C.RED}FAIL{C.RESET}"
        grade_color = C.GREEN if sub.grade in ("A+", "A") else (C.YELLOW if sub.grade in ("B+", "B") else C.RED)
        sub_rows.append([
            str(idx),
            sub.subject_name,
            f"{sub.max_marks:.0f}",
            f"{sub.marks_obtained:.1f}",
            f"{grade_color}{sub.grade}{C.RESET}",
            status_label
        ])
        idx += 1

    if not sub_rows:
        sub_rows.append(["-", "No subjects registered yet", "-", "-", "-", "-"])

    draw_table(
        headers=sub_headers,
        rows=sub_rows,
        alignments=["C", "L", "R", "R", "C", "C"],
        title="COURSE EVALUATIONS & SEMESTER MARKS"
    )

    # Academic Summary Box
    res_color = C.GREEN if student.result_status != "FAILED" else C.RED
    print(f"\n{C.BOLD}┌─ ACADEMIC SUMMARY " + "─" * (w - 23) + "┐")
    print(f"│  Total Marks  : {student.total_marks_obtained:6.1f} / {student.total_max_marks:6.1f}  │  Overall Percentage: {student.overall_percentage:5.2f}%")
    print(f"│  Semester CGPA: {student.cgpa:4.2f} / 10.00         │  Final Letter Grade: {student.grade}")
    print(f"│  Result Status: {res_color}{student.result_status:<20}{C.RESET}{C.BOLD}│  Attendance Record : {student.attendance.attended_classes}/{student.attendance.total_classes} ({student.attendance.percentage}%)")
    print("└" + "─" * (w - 3) + f"┘{C.RESET}")

    # Attendance Progress
    att_bar = render_progress_bar(student.attendance.percentage, length=24)
    print(f"  Attendance Health : {att_bar}")
    if student.attendance.is_shortage:
        print(f"  {C.RED}⚠  CRITICAL: Attendance below 75% requirement. Not eligible for exam waiver.{C.RESET}")

    # Fee Status
    fee_st = student.fees.status
    fee_color = C.GREEN if fee_st == "PAID" else (C.YELLOW if fee_st == "PARTIAL" else C.RED)
    print(f"  Tuition Fee Status: {fee_color}{fee_st}{C.RESET} | Total: Rs. {student.fees.total_fee:,.2f} | Paid: Rs. {student.fees.paid_amount:,.2f} | Due: Rs. {student.fees.due_amount:,.2f}")

    # Signatures
    print(f"\n{C.DIM}  " + "─" * (w - 4))
    print(f"  Controller of Examinations                        Dean of Academic Affairs")
    print("  [Verified Official Seal]                          [Autonomous Accreditation]")
    print("─" * (w - 4) + f"{C.RESET}")


def render_grade_distribution_chart(distribution: Dict[str, int]) -> None:
    """Render a terminal horizontal ASCII bar chart for grades."""
    print_section_header("Grade Distribution Histogram", "📊")
    total_students = sum(distribution.values())

    if total_students == 0:
        print("  No student grade data available to plot.")
        return

    max_count = max(distribution.values()) if distribution.values() else 1
    chart_bar_length = 30

    grade_colors = {
        "A+": C.GREEN,
        "A": C.GREEN,
        "B+": C.CYAN,
        "B": C.CYAN,
        "C": C.YELLOW,
        "D": C.YELLOW,
        "F": C.RED,
    }

    print(f"\n  Total Evaluated Students: {C.BOLD}{total_students}{C.RESET}\n")
    for grade, count in distribution.items():
        ratio = count / total_students
        bar_len = int(round((count / max_count) * chart_bar_length)) if max_count > 0 else 0
        bar = "█" * bar_len + "░" * (chart_bar_length - bar_len)
        color = grade_colors.get(grade, C.WHITE)

        print(f"  Grade {C.BOLD}{grade:<2}{C.RESET} │ {color}{bar}{C.RESET} │ {count:2d} students ({ratio * 100:5.1f}%)")
    print(f"         └{'─' * (chart_bar_length + 2)}┘")


# --- Robust Input Validation Prompts ---

def prompt_string(
    label: str,
    default: Optional[str] = None,
    required: bool = True
) -> str:
    """Prompt user for a string with optional default."""
    while True:
        prompt_txt = f"{C.BOLD}{label}{C.RESET}"
        if default is not None:
            prompt_txt += f" {C.DIM}[Default: {default}]{C.RESET}"
        prompt_txt += ": "

        try:
            val = input(prompt_txt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return default or ""

        if not val and default is not None:
            return default
        if not val and required:
            print_error("This field cannot be empty. Please enter a valid value.")
            continue
        return val


def prompt_int(
    label: str,
    default: Optional[int] = None,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None
) -> int:
    """Prompt user for an integer within an optional range."""
    while True:
        prompt_txt = f"{C.BOLD}{label}{C.RESET}"
        if default is not None:
            prompt_txt += f" {C.DIM}[Default: {default}]{C.RESET}"
        prompt_txt += ": "

        try:
            val_str = input(prompt_txt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return default if default is not None else 0

        if not val_str and default is not None:
            return default

        try:
            val = int(val_str)
            if min_val is not None and val < min_val:
                print_error(f"Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value cannot exceed {max_val}.")
                continue
            return val
        except ValueError:
            print_error("Invalid integer. Please enter digits only.")


def prompt_float(
    label: str,
    default: Optional[float] = None,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> float:
    """Prompt user for a floating point number within an optional range."""
    while True:
        prompt_txt = f"{C.BOLD}{label}{C.RESET}"
        if default is not None:
            prompt_txt += f" {C.DIM}[Default: {default}]{C.RESET}"
        prompt_txt += ": "

        try:
            val_str = input(prompt_txt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return default if default is not None else 0.0

        if not val_str and default is not None:
            return default

        try:
            val = float(val_str)
            if min_val is not None and val < min_val:
                print_error(f"Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value cannot exceed {max_val}.")
                continue
            return round(val, 2)
        except ValueError:
            print_error("Invalid number. Please enter a valid numeric value.")


def prompt_confirm(prompt: str, default: bool = True) -> bool:
    """Prompt user for yes/no confirmation."""
    choices_str = "[Y/n]" if default else "[y/N]"
    prompt_txt = f"{C.YELLOW}{prompt} {choices_str}: {C.RESET}"

    try:
        ans = input(prompt_txt).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n")
        return default

    if not ans:
        return default
    return ans in ("y", "yes", "true", "1")
