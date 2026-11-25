# Python Scientific & Financial Calculator Pro

A modular, zero-dependency Python CLI calculator featuring a **safe AST-based expression evaluator**, **scientific functions (`DEG`/`RAD`)**, **unit & number-base converters**, **financial calculators**, **memory registers**, **atomic JSON history persistence with backup recovery**, **CSV export**, and a comprehensive `unittest` suite.

---

## Project Structure

- `main.py` — Interactive terminal application (`CalculatorApp`) and non-interactive CLI flags (`-e/--eval`, `--deg`, `--rad`, `--precision`, `--json`).
- `calculator.py` — Core `CalculatorEngine`, safe AST expression evaluator (no `eval()`), arithmetic & scientific math functions, overflow/domain guards, and clean precision formatting.
- `converters.py` — Unit conversions (`length`, `weight`, `temperature`, `time`, `data`), integer number-base conversions (`BIN`, `OCT`, `DEC`, `HEX`), and financial utilities (`% change`, `Simple Interest`, `Compound Interest`, `Loan EMI`).
- `storage.py` — `HistoryStore` and `HistoryEntry` with atomic JSON persistence (`calculator_data.json`), automatic `.backup.json` fallback recovery, search, and UTF-8 BOM CSV export.
- `ui.py` — UTF-8 console setup, ANSI styling (`NO_COLOR` & non-TTY aware), live register status banner, Unicode history tables, and expression help reference.
- `test_calculator.py` — Unit tests and CLI smoke tests built with Python's standard `unittest`.

---

## Key Features

- **Safe Live Expression Evaluator**: Evaluate nested mathematical expressions like `2 * (3 + 4)^2`, `sqrt(144) + sin(30)`, or `ans * 1.18` directly from the main prompt or inside **Live Expression Mode**.
- **Security & Domain Protection**: Uses Python's `ast` module with strict whitelisting (blocks arbitrary code execution, attribute access, booleans, strings, and runaway exponents/factorials).
- **Scientific Math (`DEG` / `RAD`)**: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `cbrt`, `ln`, `log10`, `log(x, base)`, `log2`, `exp`, `fact`, `nPr`, `nCr`, `gcd`, `lcm`, plus constants `pi`, `e`, `tau`, `phi`.
- **Memory & Register Persistence**: `MS`, `MR`, `M+`, `M-`, `MC`, `Ans` recall, angle mode, and precision persist automatically across sessions.
- **Unit & Base Conversions**: Convert metric/imperial lengths, weights, temperatures (`C`, `F`, `K`), time, digital storage (`bit` to `TB`), and `BIN`/`OCT`/`DEC`/`HEX` integers.
- **Financial Calculators**: Percentage change, discount calculator, Simple Interest, Compound Interest, and monthly Loan EMI amortization summary.
- **History & Export**: View formatted history tables, search past calculations, recall any past result into `Ans`, and export history to `calculator_history.csv`.

---

## How to Run

Run interactively from either the workspace root or inside `Calculator/`:

```bash
python Calculator/main.py
```

### Quick CLI Expression Mode

Evaluate expressions directly from the terminal without opening the interactive menu:

```bash
python Calculator/main.py -e "2 + 3 * (4 - 1)^2"
python Calculator/main.py -e "sin(pi / 6)" --rad --json
python Calculator/main.py -e "Compound? No, math:"  # invalid expressions return exit code 1
```

Available flags:
- `-e`, `--eval <EXPR>` — Evaluate a single mathematical expression and exit.
- `--deg` / `--rad` — Select Degrees (default) or Radians for trigonometry.
- `--precision <4..15>` — Set significant digits for formatted output (default `12`).
- `--json` — Emit `--eval` output as structured JSON.

---

## Supported Expression Reference

- **Operators**: `+`, `-`, `*`, `/`, `//`, `%`, `**` or `^`, parentheses `( )`
- **Constants & Registers**: `pi`, `e`, `tau`, `phi`, `ans`, `mem` (or `m`)
- **Functions**: `abs`, `round`, `floor`, `ceil`, `sqrt`, `cbrt`, `pow`, `exp`, `ln`, `log`, `log10`, `log2`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `deg`, `rad`, `fact` (`factorial`), `pct`, `npr`, `ncr`, `gcd`, `lcm`, `min`, `max`

---

## Running Tests

```bash
python -m unittest Calculator/test_calculator.py -v
```
