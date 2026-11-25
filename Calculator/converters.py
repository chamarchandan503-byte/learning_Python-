"""Unit conversions, number-base conversions, and financial calculation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from calculator import CalculatorError, MathDomainError

# Linear conversion factors relative to a canonical base unit per category.
UNIT_CATEGORIES: dict[str, tuple[str, dict[str, float]]] = {
    "length": (
        "m",
        {
            "mm": 0.001,
            "cm": 0.01,
            "m": 1.0,
            "km": 1000.0,
            "in": 0.0254,
            "ft": 0.3048,
            "yd": 0.9144,
            "mi": 1609.344,
        },
    ),
    "weight": (
        "kg",
        {
            "mg": 1e-6,
            "g": 0.001,
            "kg": 1.0,
            "t": 1000.0,
            "oz": 0.028349523125,
            "lb": 0.45359237,
        },
    ),
    "time": (
        "s",
        {
            "ms": 0.001,
            "s": 1.0,
            "min": 60.0,
            "h": 3600.0,
            "day": 86400.0,
            "week": 604800.0,
        },
    ),
    "data": (
        "B",
        {
            "B": 1.0,
            "KB": 1024.0,
            "MB": 1024.0**2,
            "GB": 1024.0**3,
            "TB": 1024.0**4,
            "bit": 0.125,
        },
    ),
}

TEMPERATURE_UNITS = ("C", "F", "K")

NUMBER_BASES: dict[str, int] = {
    "BIN": 2,
    "OCT": 8,
    "DEC": 10,
    "HEX": 16,
}


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between Celsius (C), Fahrenheit (F), and Kelvin (K)."""
    src = from_unit.strip().upper()
    dst = to_unit.strip().upper()
    if src not in TEMPERATURE_UNITS or dst not in TEMPERATURE_UNITS:
        raise CalculatorError(f"unsupported temperature unit; choose from {', '.join(TEMPERATURE_UNITS)}")

    if src == "C":
        celsius = value
    elif src == "F":
        celsius = (value - 32.0) * (5.0 / 9.0)
    else:
        celsius = value - 273.15

    if celsius < -273.15 - 1e-9:
        raise MathDomainError("temperature cannot be below absolute zero (-273.15 °C)")

    if dst == "C":
        return celsius
    if dst == "F":
        return (celsius * 9.0 / 5.0) + 32.0
    return celsius + 273.15


def convert_unit(category: str, value: float, from_unit: str, to_unit: str) -> float:
    """Convert a value between two units in the specified category."""
    cat_key = category.strip().lower()
    if cat_key == "temperature":
        return convert_temperature(value, from_unit, to_unit)

    if cat_key not in UNIT_CATEGORIES:
        raise CalculatorError(f"unknown unit category '{category}'")

    _, unit_map = UNIT_CATEGORIES[cat_key]
    lookup = {k.lower(): k for k in unit_map}
    src_key = lookup.get(from_unit.strip().lower())
    dst_key = lookup.get(to_unit.strip().lower())
    if src_key is None or dst_key is None:
        available = ", ".join(unit_map.keys())
        raise CalculatorError(f"invalid unit for {cat_key}; available units: {available}")

    if value < 0 and cat_key in ("length", "weight", "time", "data"):
        raise MathDomainError(f"{cat_key} value cannot be negative")

    base_value = value * unit_map[src_key]
    return base_value / unit_map[dst_key]


def convert_number_base(value_str: str, from_base: str, to_base: str) -> str:
    """Convert an integer string between BIN, OCT, DEC, and HEX."""
    src = from_base.strip().upper()
    dst = to_base.strip().upper()
    if src not in NUMBER_BASES or dst not in NUMBER_BASES:
        raise CalculatorError("supported bases are BIN, OCT, DEC, and HEX")

    cleaned = value_str.strip()
    if not cleaned:
        raise CalculatorError("input number cannot be empty")

    try:
        decimal_val = int(cleaned, NUMBER_BASES[src])
    except ValueError as exc:
        raise CalculatorError(f"'{cleaned}' is not a valid {src} integer") from exc

    sign = "-" if decimal_val < 0 else ""
    magnitude = abs(decimal_val)

    if dst == "DEC":
        return f"{sign}{magnitude}"
    if dst == "BIN":
        return f"{sign}0b{bin(magnitude)[2:]}"
    if dst == "OCT":
        return f"{sign}0o{oct(magnitude)[2:]}"
    return f"{sign}0x{hex(magnitude)[2:].upper()}"


@dataclass(frozen=True)
class InterestResult:
    """Calculated interest breakdown."""

    principal: float
    interest: float
    total_amount: float


@dataclass(frozen=True)
class EmiResult:
    """Calculated monthly loan amortization summary."""

    monthly_emi: float
    total_payment: float
    total_interest: float


def percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change from old_value to new_value."""
    if old_value == 0:
        raise ZeroDivisionError("percentage change is undefined when original value is 0")
    return ((new_value - old_value) / abs(old_value)) * 100.0


def simple_interest(principal: float, annual_rate_pct: float, years: float) -> InterestResult:
    """Compute simple interest and total maturity amount."""
    if principal < 0 or annual_rate_pct < 0 or years < 0:
        raise MathDomainError("principal, rate, and time must be non-negative")
    interest = (principal * annual_rate_pct * years) / 100.0
    return InterestResult(principal=principal, interest=interest, total_amount=principal + interest)


def compound_interest(
    principal: float,
    annual_rate_pct: float,
    years: float,
    compounds_per_year: int = 1,
) -> InterestResult:
    """Compute compound interest and total maturity amount."""
    if principal < 0 or annual_rate_pct < 0 or years < 0:
        raise MathDomainError("principal, rate, and time must be non-negative")
    if compounds_per_year <= 0:
        raise MathDomainError("compounding frequency must be a positive integer")

    rate = annual_rate_pct / 100.0
    total = principal * ((1.0 + rate / compounds_per_year) ** (compounds_per_year * years))
    return InterestResult(principal=principal, interest=total - principal, total_amount=total)


def calculate_emi(principal: float, annual_rate_pct: float, months: int) -> EmiResult:
    """Compute Equated Monthly Installment (EMI) for a fixed-rate loan."""
    if principal <= 0:
        raise MathDomainError("loan principal must be greater than 0")
    if annual_rate_pct < 0:
        raise MathDomainError("interest rate cannot be negative")
    if months <= 0:
        raise MathDomainError("loan tenure in months must be greater than 0")

    if annual_rate_pct == 0:
        emi = principal / months
        return EmiResult(monthly_emi=emi, total_payment=principal, total_interest=0.0)

    monthly_rate = (annual_rate_pct / 12.0) / 100.0
    factor = (1.0 + monthly_rate) ** months
    emi = principal * monthly_rate * factor / (factor - 1.0)
    total_payment = emi * months
    return EmiResult(
        monthly_emi=emi,
        total_payment=total_payment,
        total_interest=total_payment - principal,
    )
