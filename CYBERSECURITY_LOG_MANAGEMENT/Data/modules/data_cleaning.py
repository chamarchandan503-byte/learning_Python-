"""Cybersecurity Log Management System - Log Data Cleaning & Sanitization Module

File: Data/modules/data_cleaning.py
Description: Cleans, sanitizes, normalizes, and validates cybersecurity event data.
             Supports CSV imports, Pandas DataFrames, and direct SQLite ingestion.
"""

from datetime import datetime, timezone
from pathlib import Path
import csv
import re
import sqlite3
from typing import Optional, Dict, Any, List, Union

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

VALID_STATUSES = {"SUCCESS", "FAILED", "BLOCKED"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
IP_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"


def is_valid_ipv4(ip: str) -> bool:
    """Validate if input string is a valid IPv4 address."""
    if not ip or not isinstance(ip, str):
        return False
    return bool(IP_REGEX.match(ip.strip()))


def sanitize_text(text: Optional[str]) -> str:
    """Sanitize log text to prevent log forging and CRLF injection."""
    if not text:
        return ""
    # Strip newline and carriage returns to prevent CRLF injection
    return str(text).replace("\r", " ").replace("\n", " ").strip()


def normalize_timestamp(timestamp_str: Optional[str]) -> str:
    """Standardize timestamps into ISO 8601 UTC format."""
    if not timestamp_str:
        return datetime.now(timezone.utc).isoformat()

    timestamp_str = str(timestamp_str).strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(timestamp_str.split("+")[0].split("Z")[0], fmt)
            return parsed.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue

    return datetime.now(timezone.utc).isoformat()


def clean_log_entry(raw_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Clean, sanitize, and validate an individual security log record."""
    if not raw_record or not isinstance(raw_record, dict):
        return None

    raw_ip = str(raw_record.get("source_ip", "")).strip()
    source_ip = raw_ip if is_valid_ipv4(raw_ip) else "127.0.0.1"

    raw_status = str(raw_record.get("status", "SUCCESS")).upper().strip()
    status = raw_status if raw_status in VALID_STATUSES else "FAILED"

    raw_severity = str(raw_record.get("severity", "LOW")).upper().strip()
    severity = raw_severity if raw_severity in VALID_SEVERITIES else "MEDIUM"

    raw_type = str(raw_record.get("event_type", "LOGIN")).upper().strip()
    event_type = sanitize_text(raw_type) or "UNKNOWN_EVENT"

    raw_user = raw_record.get("username")
    username = sanitize_text(raw_user) if raw_user else "anonymous"

    details = sanitize_text(raw_record.get("details", ""))
    event_time = normalize_timestamp(raw_record.get("event_time"))

    return {
        "event_time": event_time,
        "source_ip": source_ip,
        "username": username,
        "event_type": event_type,
        "status": status,
        "severity": severity,
        "details": details,
    }


def load_data(file_path: Union[str, Path]):
    """Load security logs from CSV file (supports Pandas if installed, otherwise CSV DictReader)."""
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return None

    if HAS_PANDAS:
        try:
            df = pd.read_csv(path)
            print(f"[OK] Loaded {len(df)} records using Pandas.")
            return df
        except Exception as error:
            print(f"[WARNING] Pandas failed to read CSV: {error}. Falling back to standard CSV reader.")

    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)
            print(f"[OK] Loaded {len(records)} records from CSV.")
            return records
    except Exception as error:
        print(f"[ERROR] Failed to read CSV: {error}")
        return None


def clean_data(data):
    """Clean raw security logs dataset (supports both Pandas DataFrame and List of Dicts)."""
    if data is None:
        return None

    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        df = data.copy()
        # Drop duplicates
        df = df.drop_duplicates()

        # Sanitize columns
        if "source_ip" in df.columns:
            df["source_ip"] = df["source_ip"].astype(str).apply(
                lambda ip: ip if is_valid_ipv4(ip) else "127.0.0.1"
            )
        if "status" in df.columns:
            df["status"] = df["status"].astype(str).str.upper().str.strip().apply(
                lambda s: s if s in VALID_STATUSES else "FAILED"
            )
        if "severity" in df.columns:
            df["severity"] = df["severity"].astype(str).str.upper().str.strip().apply(
                lambda s: s if s in VALID_SEVERITIES else "MEDIUM"
            )
        if "username" in df.columns:
            df["username"] = df["username"].fillna("anonymous").astype(str).apply(sanitize_text)
        if "details" in df.columns:
            df["details"] = df["details"].fillna("").astype(str).apply(sanitize_text)
        if "event_time" in df.columns:
            df["event_time"] = df["event_time"].apply(normalize_timestamp)

        return df

    # Fallback for list of dictionaries
    if isinstance(data, list):
        cleaned = [clean_log_entry(row) for row in data if row]
        return [r for r in cleaned if r is not None]

    return data


def clean_and_import_to_db(csv_path: Union[str, Path]) -> int:
    """Clean a CSV log file and import records directly into SQLite database."""
    records = load_data(csv_path)
    if records is None:
        return 0

    cleaned = clean_data(records)
    if cleaned is None:
        return 0

    if HAS_PANDAS and isinstance(cleaned, pd.DataFrame):
        rows_to_insert = cleaned.to_dict(orient="records")
    else:
        rows_to_insert = cleaned

    if not DATABASE_PATH.exists():
        print(f"[ERROR] Database not found at {DATABASE_PATH}. Run database.py first.")
        return 0

    inserted_count = 0
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            for r in rows_to_insert:
                cursor.execute("""
                    INSERT INTO security_events
                    (event_time, source_ip, username, event_type, status, severity, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    r["event_time"],
                    r["source_ip"],
                    r["username"],
                    r["event_type"],
                    r["status"],
                    r["severity"],
                    r["details"]
                ))
                inserted_count += 1
            conn.commit()
            print(f"[OK] Successfully imported {inserted_count} cleaned logs into database.")
    except sqlite3.Error as error:
        print(f"[ERROR] Database import error: {error}")

    return inserted_count


if __name__ == "__main__":
    print("=== Testing Cybersecurity Data Cleaning Module ===")
    sample_raw = {
        "source_ip": "192.168.1.100",
        "username": "  sec_admin  ",
        "event_type": "ssh_login",
        "status": "failed",
        "severity": "high",
        "details": "Invalid password\nattempt detected (CRLF injection check)!",
        "event_time": "2026-11-23 18:30:00",
    }
    cleaned = clean_log_entry(sample_raw)
    print("Cleaned Single Entry:")
    for k, v in cleaned.items():
        print(f"  {k}: {v}")

    sample_csv = Path(__file__).resolve().parent.parent / "sample_security_logs.csv"
    if sample_csv.exists():
        print(f"\nCleaning CSV: {sample_csv.name}")
        data = load_data(sample_csv)
        cleaned_dataset = clean_data(data)
        print(f"[OK] Cleaned Dataset ready with {len(cleaned_dataset)} rows.")

    sample_csv = Path(__file__).resolve().parent.parent / "sample_security_logs.csv"
    if sample_csv.exists():
        print(f"\nCleaning CSV: {sample_csv.name}")
        data = load_data(sample_csv)
        cleaned_dataset = clean_data(data)
        print(f"[OK] Cleaned Dataset ready with {len(cleaned_dataset)} rows.")

