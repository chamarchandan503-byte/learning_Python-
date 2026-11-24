"""Enterprise Cybersecurity Log Management System - Log Ingestion & Collection Engine

File: modules/log_collector.py
Description: Ingests raw security telemetry, validates attributes against RFC standards
             and security policies, sanitizes payload data, and commits to SQLite.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [LogCollector] %(message)s")
logger = logging.getLogger("LogCollector")

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"

# Strict policy enforcements
VALID_STATUSES = {"SUCCESS", "FAILED", "BLOCKED"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
IP_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)


def get_connection() -> sqlite3.Connection:
    """Return an active connection with foreign keys enabled."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def validate_ip(ip: str) -> str:
    """Sanitize and validate IPv4 address, defaulting to local loopback if invalid."""
    if not ip or not isinstance(ip, str):
        return "127.0.0.1"
    cleaned = ip.strip()
    return cleaned if IP_REGEX.match(cleaned) else "127.0.0.1"


def sanitize_input(val: Optional[str], default: str = "") -> str:
    """Strip carriage returns and newlines to prevent log injection (CRLF attack)."""
    if not val:
        return default
    return str(val).replace("\r", " ").replace("\n", " ").strip()


def collect_log(
    source_ip: str,
    username: Optional[str],
    event_type: str,
    status: str,
    severity: str,
    details: str,
    event_time: Optional[str] = None,
) -> Optional[int]:
    """Ingest, validate, and store a security event record into the database.

    Returns:
        int: The newly created database record ID, or None if validation fails.
    """
    clean_status = (status or "").upper().strip()
    clean_severity = (severity or "").upper().strip()
    clean_type = sanitize_input(event_type, default="SYSTEM_EVENT").upper()
    clean_ip = validate_ip(source_ip)
    clean_user = sanitize_input(username, default="anonymous")
    clean_details = sanitize_input(details, default="")

    if clean_status not in VALID_STATUSES:
        logger.warning("Rejected log: Invalid status '%s'. Must be in %s", clean_status, VALID_STATUSES)
        return None

    if clean_severity not in VALID_SEVERITIES:
        logger.warning("Rejected log: Invalid severity '%s'. Must be in %s", clean_severity, VALID_SEVERITIES)
        return None

    if not event_time:
        event_time = datetime.now(timezone.utc).isoformat()

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO security_events
                (event_time, source_ip, username, event_type, status, severity, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (event_time, clean_ip, clean_user, clean_type, clean_status, clean_severity, clean_details),
            )
            conn.commit()
            event_id = cursor.lastrowid
            logger.info("Security event recorded. ID: %s | Type: %s | Status: %s", event_id, clean_type, clean_status)
            return event_id

    except sqlite3.Error as err:
        logger.error("Database write failure: %s", err)
        return None


def collect_batch_logs(events: List[Dict[str, Any]]) -> int:
    """Ingest multiple log records within a single atomic database transaction.

    Returns:
        int: Total number of successfully committed records.
    """
    if not events:
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    saved = 0

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for ev in events:
                c_status = str(ev.get("status", "SUCCESS")).upper().strip()
                c_sev = str(ev.get("severity", "LOW")).upper().strip()
                if c_status in VALID_STATUSES and c_sev in VALID_SEVERITIES:
                    cursor.execute(
                        """
                        INSERT INTO security_events
                        (event_time, source_ip, username, event_type, status, severity, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ev.get("event_time") or now_iso,
                            validate_ip(ev.get("source_ip", "")),
                            sanitize_input(ev.get("username"), "anonymous"),
                            sanitize_input(ev.get("event_type"), "EVENT").upper(),
                            c_status,
                            c_sev,
                            sanitize_input(ev.get("details"), ""),
                        ),
                    )
                    saved += 1
            conn.commit()
            logger.info("Batch ingestion committed: %d/%d records stored.", saved, len(events))
            return saved
    except sqlite3.Error as err:
        logger.error("Batch collection aborted: %s", err)
        return saved


def simulate_attack_traffic(target_ip: str = "198.51.100.22", attack_type: str = "BRUTE_FORCE", attempts: int = 5):
    """Testing utility: Generates simulated security attack scenarios for detection validation."""
    logger.info("Initiating attack simulation: %s (%d events from %s)", attack_type, attempts, target_ip)

    if attack_type == "BRUTE_FORCE":
        for i in range(1, attempts + 1):
            collect_log(
                source_ip=target_ip,
                username="victim_admin",
                event_type="LOGIN",
                status="FAILED",
                severity="HIGH",
                details=f"Automated Brute-Force Simulation: Attempt {i}/{attempts}",
            )
    elif attack_type == "SQL_INJECTION":
        collect_log(
            source_ip=target_ip,
            username="anonymous",
            event_type="SQL_INJECTION",
            status="BLOCKED",
            severity="CRITICAL",
            details="Attack Simulation: Detected pattern 'admin' -- DROP TABLE users;'",
        )
    elif attack_type == "PORT_SCAN":
        collect_log(
            source_ip=target_ip,
            username="unknown",
            event_type="PORT_SCAN",
            status="BLOCKED",
            severity="HIGH",
            details="Attack Simulation: Port sweep on 10 ports in 500ms",
        )


if __name__ == "__main__":
    print("=== Testing Enterprise Log Collector ===")
    sample_id = collect_log(
        source_ip="10.10.10.5",
        username="sec_lead",
        event_type="LOGIN",
        status="SUCCESS",
        severity="LOW",
        details="SOC operator session established.",
    )
    print(f"Sample Log ID: {sample_id}")
    simulate_attack_traffic(target_ip="198.51.100.99", attack_type="BRUTE_FORCE", attempts=5)
