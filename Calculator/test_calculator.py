"""Unit and CLI smoke tests for the Professional Python Calculator."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_CALC_DIR = Path(__file__).resolve().parent
if str(_CALC_DIR) not in sys.path:
    sys.path.insert(0, str(_CALC_DIR))

from calculator import (  # noqa: E402
    CalculatorEngine,
    ExpressionError,
    MathDomainError,
    add,
    cbrt,
    combinations,
    divide,
    evaluate_expression,
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
    calculate_emi,
    compound_interest,
    convert_number_base,
    convert_unit,
    percentage_change,
    simple_interest,
)
from main import main as cli_main  # noqa: E402
from storage import HistoryStore  # noqa: E402


class TestBasicAndScientificFunctions(unittest.TestCase):
    def test_basic_arithmetic(self) -> None:
        self.assertEqual(add(10, 5), 15)
        self.assertEqual(subtract(10, 5), 5)
        self.assertEqual(multiply(4, 2.5), 10.0)
        self.assertEqual(divide(9, 2), 4.5)
        self.assertEqual(floor_divide(9, 2), 4)
        self.assertEqual(modulo(10, 3), 1)
        self.assertEqual(power(2, 5), 32.0)
        self.assertEqual(percentage(200, 15), 30.0)
        self.assertAlmostEqual(reciprocal(4), 0.25)

    def test_zero_division_errors(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            divide(10, 0)
        with self.assertRaises(ZeroDivisionError):
            floor_divide(10, 0)
        with self.assertRaises(ZeroDivisionError):
            modulo(10, 0)
        with self.assertRaises(ZeroDivisionError):
            reciprocal(0)
        with self.assertRaises(ZeroDivisionError):
            power(0, -1)

    def test_scientific_functions(self) -> None:
        self.assertEqual(sqrt(81), 9.0)
        self.assertAlmostEqual(cbrt(-27), -3.0)
        self.assertEqual(factorial(5), 120)
        self.assertEqual(factorial(0), 1)
        self.assertAlmostEqual(ln(math.e), 1.0)
        self.assertAlmostEqual(log10(1000), 3.0)
        self.assertAlmostEqual(log_base(8, 2), 3.0)
        self.assertAlmostEqual(exp(0), 1.0)
        self.assertEqual(permutations(5, 2), 20)
        self.assertEqual(combinations(5, 2), 10)
        self.assertEqual(gcd(24, 36), 12)
        self.assertEqual(lcm(4, 6), 12)

    def test_domain_and_overflow_guards(self) -> None:
        with self.assertRaises(MathDomainError):
            sqrt(-4)
        with self.assertRaises(MathDomainError):
            factorial(-1)
        with self.assertRaises(MathDomainError):
            ln(0)
        with self.assertRaises(MathDomainError):
            log_base(10, 1)
        with self.assertRaises(OverflowError):
            factorial(171)
        with self.assertRaises(OverflowError):
            power(10, 500)


class TestExpressionEngine(unittest.TestCase):
    def test_expression_evaluation_and_registers(self) -> None:
        engine = CalculatorEngine(angle_mode="DEG")
        self.assertAlmostEqual(engine.evaluate("2 + 3 * (4 - 1)^2"), 29.0)
        self.assertAlmostEqual(engine.last_answer, 29.0)
        self.assertAlmostEqual(engine.evaluate("ans + 1"), 30.0)

        engine.memory_store(10)
        engine.memory_add(5)
        engine.memory_subtract(3)
        self.assertAlmostEqual(engine.evaluate("mem * 2"), 24.0)

    def test_trigonometry_deg_and_rad(self) -> None:
        deg_engine = CalculatorEngine(angle_mode="DEG")
        self.assertAlmostEqual(deg_engine.evaluate("sin(30)"), 0.5)
        self.assertEqual(deg_engine.evaluate("cos(90)"), 0.0)
        self.assertAlmostEqual(deg_engine.evaluate("asin(0.5)"), 30.0)
        with self.assertRaises(MathDomainError):
            deg_engine.evaluate("tan(90)")

        rad_engine = CalculatorEngine(angle_mode="RAD")
        self.assertAlmostEqual(rad_engine.evaluate("sin(pi / 6)"), 0.5)
        self.assertAlmostEqual(rad_engine.evaluate("cos(pi)"), -1.0)

    def test_format_number_cleans_float_noise(self) -> None:
        result = evaluate_expression("0.1 + 0.2")
        self.assertEqual(format_number(result), "0.3")
        self.assertEqual(format_number(-0.0), "0")
        self.assertEqual(format_number(15.0), "15")

    def test_security_rejects_unsafe_ast(self) -> None:
        unsafe_inputs = [
            "__import__('os').system('echo hi')",
            "(1).__class__",
            "'hello'",
            "True + 1",
            "round(3.14, ndigits=1)",
            "unknown_var + 2",
            "open('test.txt')",
            "2 ** 1000000",
        ]
        for expr in unsafe_inputs:
            with self.assertRaises((ExpressionError, OverflowError), msg=f"Should reject: {expr}"):
                evaluate_expression(expr)


class TestConvertersAndFinancial(unittest.TestCase):
    def test_unit_conversions(self) -> None:
        self.assertAlmostEqual(convert_unit("length", 2.5, "km", "m"), 2500.0)
        self.assertAlmostEqual(convert_unit("weight", 1, "kg", "g"), 1000.0)
        self.assertAlmostEqual(convert_unit("temperature", 100, "C", "F"), 212.0)
        self.assertAlmostEqual(convert_unit("temperature", 0, "C", "K"), 273.15)
        self.assertAlmostEqual(convert_unit("data", 1, "GB", "MB"), 1024.0)

        with self.assertRaises(MathDomainError):
            convert_unit("temperature", -300, "C", "K")

    def test_number_base_conversions(self) -> None:
        self.assertEqual(convert_number_base("255", "DEC", "HEX"), "0xFF")
        self.assertEqual(convert_number_base("0b1010", "BIN", "DEC"), "10")
        self.assertEqual(convert_number_base("-42", "DEC", "BIN"), "-0b101010")
        self.assertEqual(convert_number_base("77", "OCT", "DEC"), "63")

    def test_financial_calculators(self) -> None:
        self.assertAlmostEqual(percentage_change(100, 125), 25.0)

        si = simple_interest(1000, 5, 2)
        self.assertAlmostEqual(si.interest, 100.0)
        self.assertAlmostEqual(si.total_amount, 1100.0)

        ci = compound_interest(1000, 10, 2, compounds_per_year=1)
        self.assertAlmostEqual(ci.interest, 210.0)
        self.assertAlmostEqual(ci.total_amount, 1210.0)

        emi_zero = calculate_emi(12000, 0, 12)
        self.assertAlmostEqual(emi_zero.monthly_emi, 1000.0)
        self.assertAlmostEqual(emi_zero.total_interest, 0.0)

        emi = calculate_emi(100000, 12, 12)
        self.assertAlmostEqual(emi.monthly_emi, 8884.8788678, places=4)


class TestHistoryStoreAndCLI(unittest.TestCase):
    def test_persistence_backup_recovery_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "calc.json"
            store = HistoryStore(data_path=data_file)
            store.add_entry(category="Expression", expression="2 + 3", result="5", numeric_value=5.0)
            store.add_entry(category="Scientific", expression="sin(30)", result="0.5", numeric_value=0.5)
            store.update_state(angle_mode="RAD", memory=42.0)

            # Corrupt primary file and ensure backup recovery succeeds
            data_file.write_text("{corrupt-json", encoding="utf-8")
            recovered = HistoryStore(data_path=data_file)
            self.assertTrue(recovered.recovered_from_backup)
            self.assertEqual(len(recovered.entries), 2)
            self.assertEqual(recovered.state["angle_mode"], "RAD")
            self.assertEqual(recovered.state["memory"], 42.0)

            # Search & CSV export
            self.assertEqual(len(recovered.search("sin")), 1)
            csv_path = recovered.export_csv(Path(tmpdir) / "export.csv")
            self.assertTrue(csv_path.exists())
            csv_text = csv_path.read_text(encoding="utf-8-sig")
            self.assertIn("2 + 3", csv_text)
            self.assertIn("sin(30)", csv_text)

    def test_cli_eval_flags(self) -> None:
        self.assertEqual(cli_main(["--eval", "2 + 3 * 4"]), 0)
        self.assertEqual(cli_main(["--eval", "1 / 0"]), 1)
        self.assertEqual(cli_main(["--eval", "2 + 2", "--precision", "2"]), 2)

        proc = subprocess.run(
            [sys.executable, str(_CALC_DIR / "main.py"), "-e", "sin(pi / 6)", "--rad", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["formatted"], "0.5")
        self.assertEqual(payload["angle_mode"], "RAD")


if __name__ == "__main__":
    unittest.main()
