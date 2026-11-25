"""Core mathematical engine and safe AST expression evaluator."""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass, field
from typing import Callable


class CalculatorError(ValueError):
    """Base exception for calculator domain, syntax, and evaluation errors."""


class ExpressionError(CalculatorError):
    """Raised when a mathematical expression cannot be parsed or evaluated."""


class MathDomainError(CalculatorError):
    """Raised when an operation receives arguments outside its valid domain."""


def _safe_power(a: float, b: float) -> float:
    """Compute a ** b while guarding against runaway integer/float overflow."""
    if a == 0 and b < 0:
        raise ZeroDivisionError("0 cannot be raised to a negative power")
    if a < 0 and not float(b).is_integer():
        raise MathDomainError("negative base cannot be raised to a fractional power")

    if abs(a) > 1 and b > 0:
        try:
            estimated_digits = b * math.log10(abs(a))
        except (ValueError, OverflowError) as exc:
            raise OverflowError("power result exceeds supported magnitude") from exc
        if estimated_digits > 308:
            raise OverflowError("power result exceeds floating-point range")

    try:
        result = a ** b
    except OverflowError as exc:
        raise OverflowError("power result exceeds floating-point range") from exc

    if isinstance(result, complex):
        raise MathDomainError("complex results are not supported")
    if isinstance(result, float) and (math.isinf(result) or math.isnan(result)):
        raise OverflowError("power result is not finite")
    return float(result)


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide the first number by the second."""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


def floor_divide(a: float, b: float) -> float:
    """Perform floor division (a // b)."""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a // b


def modulo(a: float, b: float) -> float:
    """Compute remainder (a % b)."""
    if b == 0:
        raise ZeroDivisionError("modulo by zero")
    return a % b


def power(base: float, exponent: float) -> float:
    """Raise base to exponent."""
    return _safe_power(base, exponent)


def percentage(value: float, percent: float) -> float:
    """Compute percent% of value."""
    return (value * percent) / 100.0


def reciprocal(x: float) -> float:
    """Return 1 / x."""
    if x == 0:
        raise ZeroDivisionError("reciprocal of zero is undefined")
    return 1.0 / x


def sqrt(x: float) -> float:
    """Return the square root of x."""
    if x < 0:
        raise MathDomainError("square root is undefined for negative numbers")
    return math.sqrt(x)


def cbrt(x: float) -> float:
    """Return the real cube root of x."""
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


def factorial(n: float) -> int:
    """Return n! for non-negative integers up to 170."""
    if not float(n).is_integer() or n < 0:
        raise MathDomainError("factorial requires a non-negative integer")
    n_int = int(n)
    if n_int > 170:
        raise OverflowError("factorial input too large (maximum supported is 170)")
    return math.factorial(n_int)


def ln(x: float) -> float:
    """Return the natural logarithm of x."""
    if x <= 0:
        raise MathDomainError("natural logarithm requires a positive number")
    return math.log(x)


def log10(x: float) -> float:
    """Return the base-10 logarithm of x."""
    if x <= 0:
        raise MathDomainError("base-10 logarithm requires a positive number")
    return math.log10(x)


def log_base(x: float, base: float) -> float:
    """Return logarithm of x with the specified base."""
    if x <= 0:
        raise MathDomainError("logarithm argument must be positive")
    if base <= 0 or base == 1:
        raise MathDomainError("logarithm base must be positive and not equal to 1")
    return math.log(x, base)


def exp(x: float) -> float:
    """Return e^x with overflow protection."""
    if x > 709:
        raise OverflowError("exponential result exceeds floating-point range")
    return math.exp(x)


def permutations(n: float, r: float) -> int:
    """Return nPr for non-negative integers with r <= n."""
    if not float(n).is_integer() or not float(r).is_integer() or n < 0 or r < 0:
        raise MathDomainError("nPr requires non-negative integers")
    n_int, r_int = int(n), int(r)
    if r_int > n_int:
        raise MathDomainError("r cannot exceed n in nPr")
    if n_int > 170:
        raise OverflowError("nPr input too large (maximum n is 170)")
    return math.perm(n_int, r_int)


def combinations(n: float, r: float) -> int:
    """Return nCr for non-negative integers with r <= n."""
    if not float(n).is_integer() or not float(r).is_integer() or n < 0 or r < 0:
        raise MathDomainError("nCr requires non-negative integers")
    n_int, r_int = int(n), int(r)
    if r_int > n_int:
        raise MathDomainError("r cannot exceed n in nCr")
    if n_int > 1000:
        raise OverflowError("nCr input too large (maximum n is 1000)")
    return math.comb(n_int, r_int)


def gcd(a: float, b: float) -> int:
    """Return greatest common divisor of two integers."""
    if not float(a).is_integer() or not float(b).is_integer():
        raise MathDomainError("gcd requires integer inputs")
    return math.gcd(int(a), int(b))


def lcm(a: float, b: float) -> int:
    """Return least common multiple of two integers."""
    if not float(a).is_integer() or not float(b).is_integer():
        raise MathDomainError("lcm requires integer inputs")
    return math.lcm(int(a), int(b))


def format_number(value: int | float, precision: int = 12) -> str:
    """Format numeric results cleanly without floating-point representation noise."""
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid numeric result")
    if isinstance(value, int):
        if abs(value) >= 10**15:
            return f"{float(value):.{precision}g}"
        return str(value)

    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"

    if value == 0.0:
        return "0"

    if abs(value) >= 1e12 or (0 < abs(value) < 1e-6):
        formatted = f"{value:.{precision}g}"
    else:
        formatted = f"{value:.{precision}g}"
        if "e" not in formatted and "E" not in formatted and "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")

    if formatted == "-0":
        return "0"
    return formatted


def normalize_number(value: float) -> int | float:
    """Return an int when a float represents an exact safe integer, else clean float."""
    if value == 0.0:
        return 0
    if isinstance(value, int):
        return value
    if math.isfinite(value) and abs(value) < 1e15 and value.is_integer():
        return int(value)
    return value


_BINARY_OPS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: add,
    ast.Sub: subtract,
    ast.Mult: multiply,
    ast.Div: divide,
    ast.FloorDiv: floor_divide,
    ast.Mod: modulo,
    ast.Pow: _safe_power,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: lambda x: +x,
    ast.USub: lambda x: -x,
}


@dataclass
class CalculatorEngine:
    """Stateful scientific calculator with angle mode, memory register, and Ans."""

    angle_mode: str = "DEG"
    last_answer: float = 0.0
    memory: float = 0.0
    precision: int = 12
    _constants: dict[str, float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.set_angle_mode(self.angle_mode)
        self._constants = {
            "pi": math.pi,
            "e": math.e,
            "tau": math.tau,
            "phi": (1.0 + math.sqrt(5.0)) / 2.0,
        }

    def set_angle_mode(self, mode: str) -> str:
        """Set angle unit to DEG or RAD."""
        normalized = mode.strip().upper()
        if normalized not in ("DEG", "RAD"):
            raise CalculatorError("angle mode must be 'DEG' or 'RAD'")
        self.angle_mode = normalized
        return self.angle_mode

    def _to_radians(self, angle: float) -> float:
        return math.radians(angle) if self.angle_mode == "DEG" else angle

    def _from_radians(self, radians_val: float) -> float:
        return math.degrees(radians_val) if self.angle_mode == "DEG" else radians_val

    def _snap_trig_zero(self, value: float) -> float:
        return 0.0 if abs(value) < 1e-15 else value

    def sin(self, x: float) -> float:
        """Sine of x using the engine's current angle mode."""
        return self._snap_trig_zero(math.sin(self._to_radians(x)))

    def cos(self, x: float) -> float:
        """Cosine of x using the engine's current angle mode."""
        return self._snap_trig_zero(math.cos(self._to_radians(x)))

    def tan(self, x: float) -> float:
        """Tangent of x using the engine's current angle mode."""
        rad = self._to_radians(x)
        if abs(math.cos(rad)) < 1e-15:
            raise MathDomainError("tangent is undefined at odd multiples of 90° (π/2 rad)")
        return self._snap_trig_zero(math.tan(rad))

    def asin(self, x: float) -> float:
        """Inverse sine of x, returned in the current angle mode."""
        if x < -1.0 or x > 1.0:
            raise MathDomainError("asin domain is [-1, 1]")
        return self._from_radians(math.asin(x))

    def acos(self, x: float) -> float:
        """Inverse cosine of x, returned in the current angle mode."""
        if x < -1.0 or x > 1.0:
            raise MathDomainError("acos domain is [-1, 1]")
        return self._from_radians(math.acos(x))

    def atan(self, x: float) -> float:
        """Inverse tangent of x, returned in the current angle mode."""
        return self._from_radians(math.atan(x))

    def memory_clear(self) -> float:
        """Reset memory register to 0."""
        self.memory = 0.0
        return self.memory

    def memory_store(self, value: float) -> float:
        """Store a value into the memory register."""
        self.memory = float(value)
        return self.memory

    def memory_add(self, value: float) -> float:
        """Add value to the memory register."""
        self.memory += float(value)
        return self.memory

    def memory_subtract(self, value: float) -> float:
        """Subtract value from the memory register."""
        self.memory -= float(value)
        return self.memory

    def memory_recall(self) -> float:
        """Return the current memory register value."""
        return self.memory

    def _functions(self) -> dict[str, tuple[Callable[..., float | int], int | tuple[int, int]]]:
        """Return mapping of function names to (callable, expected_arity)."""
        return {
            "abs": (abs, 1),
            "round": (lambda x, nd=None: round(x) if nd is None else round(x, int(nd)), (1, 2)),
            "floor": (math.floor, 1),
            "ceil": (math.ceil, 1),
            "sqrt": (sqrt, 1),
            "cbrt": (cbrt, 1),
            "pow": (power, 2),
            "exp": (exp, 1),
            "ln": (ln, 1),
            "log": (log10, (1, 2)),
            "log10": (log10, 1),
            "log2": (lambda x: log_base(x, 2.0), 1),
            "sin": (self.sin, 1),
            "cos": (self.cos, 1),
            "tan": (self.tan, 1),
            "asin": (self.asin, 1),
            "acos": (self.acos, 1),
            "atan": (self.atan, 1),
            "deg": (math.degrees, 1),
            "rad": (math.radians, 1),
            "fact": (factorial, 1),
            "factorial": (factorial, 1),
            "pct": (percentage, 2),
            "npr": (permutations, 2),
            "ncr": (combinations, 2),
            "gcd": (gcd, 2),
            "lcm": (lcm, 2),
            "min": (min, 2),
            "max": (max, 2),
        }

    def evaluate(self, expression: str, *, update_ans: bool = True) -> float:
        """Safely parse and evaluate a mathematical expression via AST."""
        cleaned = expression.strip()
        if not cleaned:
            raise ExpressionError("expression cannot be empty")
        if len(cleaned) > 500:
            raise ExpressionError("expression exceeds maximum length of 500 characters")

        # Support standard mathematical caret notation (2^3 -> 2**3)
        normalized = cleaned.replace("^", "**")

        try:
            tree = ast.parse(normalized, mode="eval")
        except SyntaxError as exc:
            raise ExpressionError(f"invalid syntax near '{exc.text.strip() if exc.text else ''}'".strip()) from exc

        result = float(self._eval_node(tree.body))
        if math.isnan(result) or math.isinf(result):
            raise OverflowError("result is not finite")

        if update_ans:
            self.last_answer = result
        return result

    def _eval_node(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ExpressionError("only numeric literals are allowed")
            return node.value

        if isinstance(node, ast.Name):
            name = node.id.lower()
            if name == "ans":
                return self.last_answer
            if name in ("mem", "m"):
                return self.memory
            if name in self._constants:
                return self._constants[name]
            raise ExpressionError(f"unknown symbol '{node.id}'")

        if isinstance(node, ast.UnaryOp):
            op_func = _UNARY_OPS.get(type(node.op))
            if op_func is None:
                raise ExpressionError("unsupported unary operator")
            return op_func(self._eval_node(node.operand))

        if isinstance(node, ast.BinOp):
            op_func = _BINARY_OPS.get(type(node.op))
            if op_func is None:
                raise ExpressionError("unsupported operator")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op_func(left, right)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ExpressionError("method calls and dynamic callables are not allowed")
            if node.keywords:
                raise ExpressionError("keyword arguments are not supported")

            func_name = node.func.id.lower()
            functions = self._functions()
            if func_name not in functions:
                raise ExpressionError(f"unknown function '{node.func.id}'")

            func, arity = functions[func_name]
            args = [self._eval_node(arg) for arg in node.args]

            if isinstance(arity, tuple):
                min_args, max_args = arity
                if not (min_args <= len(args) <= max_args):
                    raise ExpressionError(
                        f"'{node.func.id}' expects {min_args} to {max_args} arguments, got {len(args)}"
                    )
                if func_name == "log" and len(args) == 2:
                    return log_base(args[0], args[1])
            elif len(args) != arity:
                raise ExpressionError(f"'{node.func.id}' expects {arity} argument(s), got {len(args)}")

            return func(*args)

        raise ExpressionError(f"unsupported expression element: {type(node).__name__}")


def evaluate_expression(
    expression: str,
    *,
    angle_mode: str = "DEG",
    last_answer: float = 0.0,
    memory: float = 0.0,
) -> float:
    """Convenience stateless wrapper to evaluate a mathematical expression."""
    engine = CalculatorEngine(angle_mode=angle_mode, last_answer=last_answer, memory=memory)
    return engine.evaluate(expression, update_ans=False)
