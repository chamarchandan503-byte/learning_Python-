"""Terminal presentation, ANSI styling, status bar, and formatted tables."""

from __future__ import annotations

import os
import sys

from calculator import CalculatorEngine, format_number
from storage import HistoryEntry


def configure_console() -> None:
    """Enable UTF-8 output and Windows ANSI escape sequence support when available."""
    if os.name == "nt":
        os.system("")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


class Style:
    """ANSI color styling helper that automatically degrades for non-TTY/NO_COLOR."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    @classmethod
    def enabled(cls) -> bool:
        return not os.environ.get("NO_COLOR") and sys.stdout.isatty()

    @classmethod
    def paint(cls, text: str, *codes: str) -> str:
        if not cls.enabled() or not codes:
            return text
        return f"{''.join(codes)}{text}{cls.RESET}"


def print_success(message: str) -> None:
    print(Style.paint(f"✔ {message}", Style.GREEN, Style.BOLD))


def print_error(message: str) -> None:
    print(Style.paint(f"✘ {message}", Style.RED, Style.BOLD))


def print_warning(message: str) -> None:
    print(Style.paint(f"⚠ {message}", Style.YELLOW, Style.BOLD))


def print_info(message: str) -> None:
    print(Style.paint(f"ℹ {message}", Style.CYAN))


def truncate_text(text: str, max_len: int) -> str:
    """Truncate text cleanly with ellipsis when exceeding max_len."""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def render_banner(engine: CalculatorEngine, history_count: int) -> None:
    """Render the calculator header and live register status bar."""
    width = 76
    border = "─" * width
    ans_str = format_number(engine.last_answer, engine.precision)
    mem_str = format_number(engine.memory, engine.precision)

    print()
    print(Style.paint(f"┌{border}┐", Style.CYAN))
    title = "PYTHON SCIENTIFIC & FINANCIAL CALCULATOR PRO"
    print(Style.paint("│", Style.CYAN) + Style.paint(title.center(width), Style.BOLD, Style.WHITE) + Style.paint("│", Style.CYAN))
    status = (
        f" Mode: {engine.angle_mode}  │  Ans: {ans_str}  │  Mem: {mem_str}  "
        f"│  Prec: {engine.precision}  │  Hist: {history_count} "
    )
    print(
        Style.paint("│", Style.CYAN)
        + Style.paint(truncate_text(status, width).center(width), Style.GRAY)
        + Style.paint("│", Style.CYAN)
    )
    print(Style.paint(f"└{border}┘", Style.CYAN))


def render_main_menu() -> None:
    """Display the main navigation menu."""
    print(Style.paint("  Main Menu", Style.BOLD, Style.CYAN))
    options = [
        ("1", "Live Expression Mode", "Type formulas like 2*(3+4), sin(30), sqrt(ans)"),
        ("2", "Standard Arithmetic", "+, -, *, /, //, %, x^y, 1/x, percentage"),
        ("3", "Scientific Functions", "Trig, inverse trig, log/ln, factorial, nPr/nCr, GCD/LCM"),
        ("4", "Unit & Base Converter", "Length, Weight, Temp, Time, Data, BIN/OCT/DEC/HEX"),
        ("5", "Financial Calculators", "% Change, Discount, Simple/Compound Interest, Loan EMI"),
        ("6", "Memory & Settings", "MS, MR, M+, M-, MC, DEG/RAD toggle, Precision"),
        ("7", "History & Export", "View, Search, Recall to Ans, Export CSV, Clear"),
        ("0", "Exit", "Save state and close calculator"),
    ]
    for key, label, desc in options:
        key_fmt = Style.paint(f"[{key}]", Style.YELLOW, Style.BOLD)
        label_fmt = Style.paint(f"{label:<23}", Style.WHITE, Style.BOLD)
        desc_fmt = Style.paint(desc, Style.GRAY)
        print(f"   {key_fmt} {label_fmt} {desc_fmt}")
    print(Style.paint("  Tip: You can also type any math expression directly at the prompt.", Style.DIM))


def render_result(label: str, result_text: str) -> None:
    """Display a highlighted calculation result."""
    print(
        f"  {Style.paint(label, Style.GRAY)} "
        f"{Style.paint('=', Style.CYAN, Style.BOLD)} "
        f"{Style.paint(result_text, Style.GREEN, Style.BOLD)}"
    )


def render_expression_help() -> None:
    """Display available operators, constants, functions, and REPL commands."""
    print()
    print(Style.paint("  Live Expression Reference", Style.BOLD, Style.CYAN))
    print("  Operators : +  -  *  /  //  %  ** (or ^)  ( )")
    print("  Constants : pi, e, tau, phi, ans (last result), mem (memory)")
    print("  Functions : abs, round, floor, ceil, sqrt, cbrt, pow(x,y), exp")
    print("              ln, log (base 10 or log(x,b)), log2, sin, cos, tan,")
    print("              asin, acos, atan, deg, rad, fact, npr, ncr, gcd, lcm")
    print("  Commands  : deg | rad | m+ | m- | ms | mr | mc | hist | clear | back")
    print()


def render_history_table(entries: list[HistoryEntry], title: str = "Calculation History") -> None:
    """Render calculation history in a clean Unicode table."""
    if not entries:
        print_info("No calculation history recorded yet.")
        return

    print()
    print(Style.paint(f"  {title} ({len(entries)} record(s))", Style.BOLD, Style.CYAN))
    headers = ("ID", "Timestamp", "Category", "Expression", "Result", "Mode")
    widths = (4, 19, 13, 28, 16, 4)

    top = "  ┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
    mid = "  ├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
    bot = "  └" + "┴".join("─" * (w + 2) for w in widths) + "┘"

    print(Style.paint(top, Style.GRAY))
    header_cells = [f" {h:<{w}} " for h, w in zip(headers, widths)]
    print(Style.paint("  │", Style.GRAY) + Style.paint("│", Style.GRAY).join(Style.paint(c, Style.BOLD, Style.WHITE) for c in header_cells) + Style.paint("│", Style.GRAY))
    print(Style.paint(mid, Style.GRAY))

    for entry in entries:
        row = (
            str(entry.id),
            truncate_text(entry.timestamp, widths[1]),
            truncate_text(entry.category, widths[2]),
            truncate_text(entry.expression, widths[3]),
            truncate_text(entry.result, widths[4]),
            truncate_text(entry.angle_mode, widths[5]),
        )
        cells = [f" {val:<{w}} " for val, w in zip(row, widths)]
        print(
            Style.paint("  │", Style.GRAY)
            + Style.paint("│", Style.GRAY).join(cells)
            + Style.paint("│", Style.GRAY)
        )

    print(Style.paint(bot, Style.GRAY))
