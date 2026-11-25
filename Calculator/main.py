"""Interactive and command-line entrypoint for the Professional Python Calculator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from calculator import (  # noqa: E402
    CalculatorEngine,
    CalculatorError,
    add,
    cbrt,
    combinations,
    divide,
    exp,
    factorial,
    floor_divide,
    format_number,
    gcd,
    lcm,
    ln,
    log10,
    log_base,
    modulo,
    multiply,
    percentage,
    permutations,
    power,
    reciprocal,
    sqrt,
    subtract,
)
from converters import (  # noqa: E402
    NUMBER_BASES,
    TEMPERATURE_UNITS,
    UNIT_CATEGORIES,
    calculate_emi,
    compound_interest,
    convert_number_base,
    convert_unit,
    percentage_change,
    simple_interest,
)
from storage import HistoryStore  # noqa: E402
from ui import (  # noqa: E402
    Style,
    configure_console,
    print_error,
    print_info,
    print_success,
    print_warning,
    render_banner,
    render_expression_help,
    render_history_table,
    render_main_menu,
    render_result,
)


class CalculatorApp:
    """Interactive terminal controller connecting engine, converters, storage, and UI."""

    def __init__(self, store: HistoryStore | None = None) -> None:
        self.store = store or HistoryStore()
        self.engine = CalculatorEngine(
            angle_mode=str(self.store.state.get("angle_mode", "DEG")),
            last_answer=float(self.store.state.get("last_answer", 0.0)),
            memory=float(self.store.state.get("memory", 0.0)),
            precision=int(self.store.state.get("precision", 12)),
        )

    def _sync_state(self) -> None:
        self.store.update_state(
            angle_mode=self.engine.angle_mode,
            memory=self.engine.memory,
            last_answer=self.engine.last_answer,
            precision=self.engine.precision,
        )

    def _record_numeric(self, category: str, expression: str, value: int | float) -> str:
        numeric = float(value)
        self.engine.last_answer = numeric
        formatted = format_number(value, self.engine.precision)
        self.store.state["last_answer"] = numeric
        self.store.state["angle_mode"] = self.engine.angle_mode
        self.store.state["memory"] = self.engine.memory
        self.store.state["precision"] = self.engine.precision
        self.store.add_entry(
            category=category,
            expression=expression,
            result=formatted,
            numeric_value=numeric,
            angle_mode=self.engine.angle_mode,
        )
        return formatted

    def _prompt(self, label: str) -> str:
        return input(Style.paint(label, Style.BOLD)).strip()

    def _prompt_number(self, label: str, *, allow_expr: bool = True) -> float | None:
        """Prompt for a number or expression (supports 'ans', 'mem', or 'back')."""
        raw = self._prompt(f"{label} (or 'back'): ")
        if not raw or raw.lower() in ("back", "b", "cancel"):
            return None
        if allow_expr:
            return self.engine.evaluate(raw, update_ans=False)
        try:
            return float(raw)
        except ValueError as exc:
            raise CalculatorError(f"invalid number '{raw}'") from exc

    def _evaluate_and_display(self, expr: str) -> None:
        result = self.engine.evaluate(expr, update_ans=True)
        formatted = self._record_numeric("Expression", expr, result)
        render_result(expr, formatted)

    def run(self) -> None:
        """Start the interactive menu loop."""
        configure_console()
        if self.store.recovered_from_backup:
            print_warning("Primary data file was corrupted; history and state were restored from backup.")

        while True:
            render_banner(self.engine, len(self.store.entries))
            render_main_menu()

            try:
                choice = self._prompt("\nSelect option [0-7] or expression: ")
            except (EOFError, KeyboardInterrupt):
                print()
                self._sync_state()
                print_info("State saved. Goodbye!")
                break

            if not choice:
                continue

            lowered = choice.lower()
            if lowered in ("0", "exit", "quit", "q"):
                self._sync_state()
                print_success("State saved. Thank you for using Python Calculator Pro!")
                break

            handlers = {
                "1": self.live_expression_mode,
                "2": self.standard_arithmetic_menu,
                "3": self.scientific_menu,
                "4": self.converter_menu,
                "5": self.financial_menu,
                "6": self.memory_settings_menu,
                "7": self.history_menu,
            }

            handler = handlers.get(choice)
            if handler is not None:
                try:
                    handler()
                except (EOFError, KeyboardInterrupt):
                    print()
                    print_warning("Returned to main menu.")
            else:
                try:
                    self._evaluate_and_display(choice)
                except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
                    print_error(str(exc))

    def live_expression_mode(self) -> None:
        """Continuous mathematical expression REPL with quick register commands."""
        render_expression_help()
        while True:
            ans_str = format_number(self.engine.last_answer, self.engine.precision)
            mem_str = format_number(self.engine.memory, self.engine.precision)
            prompt = f"calc [{self.engine.angle_mode} | Ans={ans_str} | M={mem_str}]> "
            raw = self._prompt(prompt)
            if not raw:
                continue

            cmd = raw.lower()
            if cmd in ("back", "exit", "quit", "q"):
                return
            if cmd in ("help", "?"):
                render_expression_help()
                continue
            if cmd in ("deg", "rad"):
                self.engine.set_angle_mode(cmd)
                self._sync_state()
                print_success(f"Angle mode switched to {self.engine.angle_mode}.")
                continue
            if cmd == "mc":
                self.engine.memory_clear()
                self._sync_state()
                print_success("Memory cleared (M = 0).")
                continue
            if cmd == "mr":
                print_info(f"Memory (M) = {format_number(self.engine.memory, self.engine.precision)}")
                continue
            if cmd == "ms":
                self.engine.memory_store(self.engine.last_answer)
                self._sync_state()
                print_success(f"Stored Ans into Memory: M = {format_number(self.engine.memory, self.engine.precision)}")
                continue
            if cmd == "m+":
                self.engine.memory_add(self.engine.last_answer)
                self._sync_state()
                print_success(f"Added Ans to Memory: M = {format_number(self.engine.memory, self.engine.precision)}")
                continue
            if cmd == "m-":
                self.engine.memory_subtract(self.engine.last_answer)
                self._sync_state()
                print_success(f"Subtracted Ans from Memory: M = {format_number(self.engine.memory, self.engine.precision)}")
                continue
            if cmd in ("hist", "history"):
                render_history_table(self.store.entries[-15:], "Recent History (Last 15)")
                continue
            if cmd == "clear":
                removed = self.store.clear()
                print_success(f"Cleared {removed} history entries.")
                continue

            try:
                self._evaluate_and_display(raw)
            except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
                print_error(str(exc))

    def standard_arithmetic_menu(self) -> None:
        """Guided arithmetic operations."""
        ops = {
            "1": ("Addition", "+", add),
            "2": ("Subtraction", "-", subtract),
            "3": ("Multiplication", "*", multiply),
            "4": ("Division", "/", divide),
            "5": ("Floor Division", "//", floor_divide),
            "6": ("Modulo", "%", modulo),
            "7": ("Power", "^", power),
            "8": ("Percentage (X% of Y)", "% of", lambda p, v: percentage(v, p)),
        }
        while True:
            print()
            print(Style.paint("  Standard Arithmetic", Style.BOLD, Style.CYAN))
            for key, (name, sym, _) in ops.items():
                print(f"   [{key}] {name} ({sym})")
            print("   [9] Reciprocal (1 / x)")
            print("   [0] Back to Main Menu")

            choice = self._prompt("Choose operation: ")
            if choice in ("0", "back", "b"):
                return

            try:
                if choice == "9":
                    x = self._prompt_number("Enter number x")
                    if x is None:
                        continue
                    res = reciprocal(x)
                    expr = f"1 / {format_number(x, self.engine.precision)}"
                    render_result(expr, self._record_numeric("Arithmetic", expr, res))
                    continue

                if choice not in ops:
                    print_error("Invalid selection.")
                    continue

                name, sym, fn = ops[choice]
                label1 = "Enter percentage (%)" if choice == "8" else "Enter first number"
                label2 = "Enter base value" if choice == "8" else "Enter second number"

                a = self._prompt_number(label1)
                if a is None:
                    continue
                b = self._prompt_number(label2)
                if b is None:
                    continue

                res = fn(a, b)
                a_s = format_number(a, self.engine.precision)
                b_s = format_number(b, self.engine.precision)
                expr = f"{a_s}% of {b_s}" if choice == "8" else f"{a_s} {sym} {b_s}"
                render_result(f"{name}: {expr}", self._record_numeric("Arithmetic", expr, res))
            except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
                print_error(str(exc))

    def scientific_menu(self) -> None:
        """Guided scientific functions menu."""
        unary_ops = {
            "1": ("Square Root", "sqrt", sqrt),
            "2": ("Cube Root", "cbrt", cbrt),
            "3": ("Factorial", "fact", factorial),
            "4": ("Natural Log", "ln", ln),
            "5": ("Log Base 10", "log10", log10),
            "6": ("Exponential (e^x)", "exp", exp),
            "7": ("Sine", "sin", self.engine.sin),
            "8": ("Cosine", "cos", self.engine.cos),
            "9": ("Tangent", "tan", self.engine.tan),
            "10": ("Inverse Sine", "asin", self.engine.asin),
            "11": ("Inverse Cosine", "acos", self.engine.acos),
            "12": ("Inverse Tangent", "atan", self.engine.atan),
        }
        binary_ops = {
            "13": ("Log Base B", "log", log_base, "Enter value x", "Enter base b"),
            "14": ("Permutations (nPr)", "nPr", permutations, "Enter n", "Enter r"),
            "15": ("Combinations (nCr)", "nCr", combinations, "Enter n", "Enter r"),
            "16": ("GCD", "gcd", gcd, "Enter integer a", "Enter integer b"),
            "17": ("LCM", "lcm", lcm, "Enter integer a", "Enter integer b"),
        }

        while True:
            print()
            print(Style.paint(f"  Scientific Functions (Angle Mode: {self.engine.angle_mode})", Style.BOLD, Style.CYAN))
            print("   [1] sqrt(x)      [2] cbrt(x)      [3] x! (fact)    [4] ln(x)")
            print("   [5] log10(x)     [6] exp(x)       [7] sin(x)       [8] cos(x)")
            print("   [9] tan(x)      [10] asin(x)     [11] acos(x)     [12] atan(x)")
            print("  [13] log_b(x)    [14] nPr         [15] nCr         [16] gcd(a,b)")
            print("  [17] lcm(a,b)    [18] Toggle DEG/RAD                [0] Back")

            choice = self._prompt("Choose function: ")
            if choice in ("0", "back", "b"):
                return
            if choice == "18":
                new_mode = "RAD" if self.engine.angle_mode == "DEG" else "DEG"
                self.engine.set_angle_mode(new_mode)
                self._sync_state()
                print_success(f"Angle mode switched to {new_mode}.")
                continue

            try:
                if choice in unary_ops:
                    name, fname, fn = unary_ops[choice]
                    x = self._prompt_number(f"{name} â€” enter x")
                    if x is None:
                        continue
                    res = fn(x)
                    expr = f"{fname}({format_number(x, self.engine.precision)})"
                    render_result(expr, self._record_numeric("Scientific", expr, res))
                elif choice in binary_ops:
                    name, fname, fn, lbl1, lbl2 = binary_ops[choice]
                    a = self._prompt_number(f"{name} â€” {lbl1}")
                    if a is None:
                        continue
                    b = self._prompt_number(f"{name} â€” {lbl2}")
                    if b is None:
                        continue
                    res = fn(a, b)
                    expr = f"{fname}({format_number(a, self.engine.precision)}, {format_number(b, self.engine.precision)})"
                    render_result(expr, self._record_numeric("Scientific", expr, res))
                else:
                    print_error("Invalid selection.")
            except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
                print_error(str(exc))

    def converter_menu(self) -> None:
        """Unit and number-base conversion menu."""
        categories = {
            "1": "length",
            "2": "weight",
            "3": "temperature",
            "4": "time",
            "5": "data",
        }
        while True:
            print()
            print(Style.paint("  Unit & Number Base Converter", Style.BOLD, Style.CYAN))
            print("   [1] Length       (mm, cm, m, km, in, ft, yd, mi)")
            print("   [2] Weight       (mg, g, kg, t, oz, lb)")
            print("   [3] Temperature  (C, F, K)")
            print("   [4] Time         (ms, s, min, h, day, week)")
            print("   [5] Data Storage (bit, B, KB, MB, GB, TB)")
            print("   [6] Number Base  (BIN, OCT, DEC, HEX)")
            print("   [0] Back to Main Menu")

            choice = self._prompt("Choose converter: ")
            if choice in ("0", "back", "b"):
                return

            try:
                if choice in categories:
                    cat = categories[choice]
                    units = TEMPERATURE_UNITS if cat == "temperature" else tuple(UNIT_CATEGORIES[cat][1].keys())
                    print_info(f"Available {cat} units: {', '.join(units)}")
                    val = self._prompt_number("Enter value")
                    if val is None:
                        continue
                    src = self._prompt("From unit: ")
                    dst = self._prompt("To unit: ")
                    converted = convert_unit(cat, val, src, dst)
                    expr = f"{format_number(val, self.engine.precision)} {src} -> {dst}"
                    formatted = self._record_numeric("Converter", expr, converted)
                    render_result(expr, f"{formatted} {dst}")
                elif choice == "6":
                    print_info(f"Supported bases: {', '.join(NUMBER_BASES.keys())}")
                    src_base = self._prompt("From base (BIN/OCT/DEC/HEX): ")
                    dst_base = self._prompt("To base (BIN/OCT/DEC/HEX): ")
                    raw_val = self._prompt("Enter integer value: ")
                    converted_str = convert_number_base(raw_val, src_base, dst_base)
                    expr = f"{raw_val} ({src_base.upper()}) -> {dst_base.upper()}"
                    self.store.add_entry(
                        category="BaseConv",
                        expression=expr,
                        result=converted_str,
                        numeric_value=None,
                        angle_mode=self.engine.angle_mode,
                    )
                    render_result(expr, converted_str)
                else:
                    print_error("Invalid selection.")
            except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
                print_error(str(exc))

    def financial_menu(self) -> None:
        """Percentage change, discount/tax, interest, and EMI calculators."""
        while True:
            print()
            print(Style.paint("  Financial & Utility Calculators", Style.BOLD, Style.CYAN))
            print("   [1] Percentage Change (Old -> New)")
            print("   [2] Discount & Final Price")
            print("   [3] Simple Interest")
            print("   [4] Compound Interest")
            print("   [5] Loan EMI Calculator")
            print("   [0] Back to Main Menu")

            choice = self._prompt("Choose calculator: ")
            if choice in ("0", "back", "b"):
                return

            try:
                if choice == "1":
                    old_val = self._prompt_number("Original value")
                    if old_val is None:
                        continue
                    new_val = self._prompt_number("New value")
                    if new_val is None:
                        continue
                    pct = percentage_change(old_val, new_val)
                    expr = f"% change({format_number(old_val)}, {format_number(new_val)})"
                    formatted = self._record_numeric("Financial", expr, pct)
                    render_result(expr, f"{formatted}%")
                elif choice == "2":
                    price = self._prompt_number("Original price")
                    if price is None:
                        continue
                    disc = self._prompt_number("Discount (%)")
                    if disc is None:
                        continue
                    saved = percentage(price, disc)
                    final_price = price - saved
                    expr = f"Price {format_number(price)} - {format_number(disc)}%"
                    formatted = self._record_numeric("Financial", expr, final_price)
                    print_info(f"You save: {format_number(saved, self.engine.precision)}")
                    render_result("Final Price", formatted)
                elif choice == "3":
                    p = self._prompt_number("Principal amount")
                    if p is None:
                        continue
                    r = self._prompt_number("Annual interest rate (%)")
                    if r is None:
                        continue
                    t = self._prompt_number("Time period (years)")
                    if t is None:
                        continue
                    res = simple_interest(p, r, t)
                    expr = f"SI(P={format_number(p)}, R={format_number(r)}%, T={format_number(t)}y)"
                    formatted = self._record_numeric("Financial", expr, res.total_amount)
                    print_info(f"Interest Earned : {format_number(res.interest, self.engine.precision)}")
                    render_result("Total Amount", formatted)
                elif choice == "4":
                    p = self._prompt_number("Principal amount")
                    if p is None:
                        continue
                    r = self._prompt_number("Annual interest rate (%)")
                    if r is None:
                        continue
                    t = self._prompt_number("Time period (years)")
                    if t is None:
                        continue
                    n = self._prompt_number("Compounds per year (1=Annual, 4=Quarterly, 12=Monthly)")
                    if n is None:
                        continue
                    if not float(n).is_integer() or n <= 0:
                        raise CalculatorError("compounds per year must be a positive integer")
                    res = compound_interest(p, r, t, int(n))
                    expr = f"CI(P={format_number(p)}, R={format_number(r)}%, T={format_number(t)}y, n={int(n)})"
                    formatted = self._record_numeric("Financial", expr, res.total_amount)
                    print_info(f"Interest Earned : {format_number(res.interest, self.engine.precision)}")
                    render_result("Maturity Amount", formatted)
                elif choice == "5":
                    p = self._prompt_number("Loan principal")
                    if p is None:
                        continue
                    r = self._prompt_number("Annual interest rate (%)")
                    if r is None:
                        continue
                    m = self._prompt_number("Tenure (months)")
                    if m is None:
                        continue
                    if not float(m).is_integer() or m <= 0:
                        raise CalculatorError("tenure in months must be a positive integer")
                    res = calculate_emi(p, r, int(m))
                    expr = f"EMI(P={format_number(p)}, R={format_number(r)}%, N={int(m)}m)"
                    formatted = self._record_numeric("Financial", expr, res.monthly_emi)
                    render_result("Monthly EMI", formatted)
                    print_info(f"Total Interest  : {format_number(res.total_interest, self.engine.precision)}")
                    print_info(f"Total Payment   : {format_number(res.total_payment, self.engine.precision)}")
                else:
                    print_error("Invalid selection.")
            except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
                print_error(str(exc))

    def memory_settings_menu(self) -> None:
        """Manage memory registers, angle mode, and precision."""
        while True:
            print()
            print(Style.paint("  Memory & Calculator Settings", Style.BOLD, Style.CYAN))
            print_info(
                f"Current -> Mode: {self.engine.angle_mode} | "
                f"Ans: {format_number(self.engine.last_answer, self.engine.precision)} | "
                f"Memory (M): {format_number(self.engine.memory, self.engine.precision)} | "
                f"Precision: {self.engine.precision}"
            )
            print("   [1] MS â€” Store value (or Ans) to Memory")
            print("   [2] M+ â€” Add value (or Ans) to Memory")
            print("   [3] M- â€” Subtract value (or Ans) from Memory")
            print("   [4] MC â€” Clear Memory (reset to 0)")
            print("   [5] Toggle Angle Mode (DEG / RAD)")
            print("   [6] Set Display Precision (4 to 15 significant digits)")
            print("   [0] Back to Main Menu")

            choice = self._prompt("Choose option: ")
            if choice in ("0", "back", "b"):
                return

            try:
                if choice in ("1", "2", "3"):
                    raw = self._prompt("Enter number/expression (leave blank to use Ans): ")
                    val = self.engine.last_answer if not raw else self.engine.evaluate(raw, update_ans=False)
                    if choice == "1":
                        self.engine.memory_store(val)
                        msg = "Stored in Memory"
                    elif choice == "2":
                        self.engine.memory_add(val)
                        msg = "Added to Memory"
                    else:
                        self.engine.memory_subtract(val)
                        msg = "Subtracted from Memory"
                    self._sync_state()
                    print_success(f"{msg}: M = {format_number(self.engine.memory, self.engine.precision)}")
                elif choice == "4":
                    self.engine.memory_clear()
                    self._sync_state()
                    print_success("Memory cleared (M = 0).")
                elif choice == "5":
                    next_mode = "RAD" if self.engine.angle_mode == "DEG" else "DEG"
                    self.engine.set_angle_mode(next_mode)
                    self._sync_state()
                    print_success(f"Angle mode set to {next_mode}.")
                elif choice == "6":
                    raw_prec = self._prompt("Enter precision (4-15): ")
                    prec = int(raw_prec)
                    if not (4 <= prec <= 15):
                        raise CalculatorError("precision must be between 4 and 15")
                    self.engine.precision = prec
                    self._sync_state()
                    print_success(f"Display precision updated to {prec} significant digits.")
                else:
                    print_error("Invalid selection.")
            except (ValueError, CalculatorError) as exc:
                print_error(str(exc))

    def history_menu(self) -> None:
        """Browse, search, recall, export, or clear calculation history."""
        while True:
            print()
            print(Style.paint(f"  History & Export ({len(self.store.entries)} total)", Style.BOLD, Style.CYAN))
            print("   [1] View Recent History (Last 20)")
            print("   [2] View Full History")
            print("   [3] Search History")
            print("   [4] Recall History Result to Ans")
            print("   [5] Export History to CSV")
            print("   [6] Clear All History")
            print("   [0] Back to Main Menu")

            choice = self._prompt("Choose option: ")
            if choice in ("0", "back", "b"):
                return

            if choice == "1":
                render_history_table(self.store.entries[-20:], "Recent History (Last 20)")
            elif choice == "2":
                render_history_table(self.store.entries, "Full Calculation History")
            elif choice == "3":
                query = self._prompt("Search keyword: ")
                matches = self.store.search(query)
                render_history_table(matches, f"Search Results for '{query}'")
            elif choice == "4":
                raw_id = self._prompt("Enter History ID to recall into Ans: ")
                try:
                    entry_id = int(raw_id)
                except ValueError:
                    print_error("Please enter a valid numeric ID.")
                    continue
                entry = self.store.get_by_id(entry_id)
                if entry is None:
                    print_error(f"No history record found with ID {entry_id}.")
                elif entry.numeric_value is None:
                    print_warning("Selected entry has no numeric value to store in Ans.")
                else:
                    self.engine.last_answer = entry.numeric_value
                    self._sync_state()
                    print_success(
                        f"Recalled #{entry.id} ({entry.expression}): "
                        f"Ans = {format_number(self.engine.last_answer, self.engine.precision)}"
                    )
            elif choice == "5":
                if not self.store.entries:
                    print_warning("History is empty; nothing to export.")
                    continue
                path = self.store.export_csv()
                print_success(f"Exported {len(self.store.entries)} record(s) to {path}")
            elif choice == "6":
                confirm = self._prompt("Are you sure you want to clear all history? (y/N): ").lower()
                if confirm in ("y", "yes"):
                    count = self.store.clear()
                    print_success(f"Cleared {count} history record(s).")
                else:
                    print_info("Clear history cancelled.")
            else:
                print_error("Invalid selection.")


def build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for non-interactive and interactive launches."""
    parser = argparse.ArgumentParser(
        prog="calculator",
        description="Professional Python Scientific, Unit & Financial Calculator.",
    )
    parser.add_argument(
        "-e",
        "--eval",
        dest="expression",
        help="Evaluate a single mathematical expression and exit.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--deg", action="store_true", help="Use degrees for trigonometry (default).")
    mode_group.add_argument("--rad", action="store_true", help="Use radians for trigonometry.")
    parser.add_argument(
        "--precision",
        type=int,
        default=12,
        help="Significant digits for formatted output (4-15, default: 12).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output --eval result as JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run CLI expression evaluation or launch the interactive calculator."""
    configure_console()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not (4 <= args.precision <= 15):
        print_error("--precision must be between 4 and 15.")
        return 2

    if args.expression is not None:
        angle_mode = "RAD" if args.rad else "DEG"
        engine = CalculatorEngine(angle_mode=angle_mode, precision=args.precision)
        try:
            result = engine.evaluate(args.expression, update_ans=False)
        except (CalculatorError, ZeroDivisionError, OverflowError) as exc:
            if args.json:
                print(json.dumps({"error": str(exc), "expression": args.expression}))
            else:
                print_error(str(exc))
            return 1

        formatted = format_number(result, args.precision)
        if args.json:
            print(
                json.dumps(
                    {
                        "expression": args.expression,
                        "result": result,
                        "formatted": formatted,
                        "angle_mode": angle_mode,
                    }
                )
            )
        else:
            print(formatted)
        return 0

    app = CalculatorApp()
    if args.rad:
        app.engine.set_angle_mode("RAD")
    elif args.deg:
        app.engine.set_angle_mode("DEG")
    app.engine.precision = args.precision
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
