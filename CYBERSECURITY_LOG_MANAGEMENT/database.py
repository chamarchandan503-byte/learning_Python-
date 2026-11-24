"""Enterprise Cybersecurity Log Management System - Database Configuration & Management

File: database.py
Description: Handles SQLite connections, schema initialization, performance PRAGMAs,
             and sample dataset population.
"""

from contextlib import contextmanager 
from datetime import datetime, timezone, timedelta
import logging
from pathlib import Path
import sqlite3
from typing import Generator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Database")

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"

# Schema discovery with case-insensitive path fallback
SCHEMA_PATH = BASE_DIR / "Database" / "schema.sql"
if not SCHEMA_PATH.exists():
    SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection(row_factory: bool = False) -> sqlite3.Connection:
    """Create and return an optimized SQLite database connection."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=20.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session(row_factory: bool = False) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database session scope."""
    conn = get_connection(row_factory=row_factory)
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Database transaction rollback due to error: %s", exc)
        raise exc
    finally:
        conn.close()


def initialize_database() -> bool:
    """Read schema.sql and create all tables and indexes."""
    if not SCHEMA_PATH.exists():
        logger.error("Database schema file not found at: %s", SCHEMA_PATH)
        return False

    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        with db_session() as conn:
            conn.executescript(schema_sql)
            conn.execute(
                "INSERT INTO system_audit_logs (action, details) VALUES (?, ?)",
                ("DATABASE_INITIALIZED", "Schema loaded and performance indexes created."),
            )
        logger.info("Database initialized successfully at: %s", DATABASE_PATH)
        return True
    except (sqlite3.Error, OSError) as error:
        logger.error("Failed to initialize database: %s", error)
        return False


def seed_sample_data(force: bool = False) -> None:
    """Populate database with enterprise-grade realistic cybersecurity event telemetry."""
    try:
        with db_session(row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM security_events")
            count = cursor.fetchone()[0]

            if count > 0 and not force:
                logger.info("Database already contains %d events. Skipping seed.", count)
                return

            now = datetime.now(timezone.utc)

            # High-fidelity realistic security telemetry
            events = [
                # Legitimate Analyst Session
                (
                    (now - timedelta(minutes=55)).isoformat(),
                    "192.168.1.10",
                    "admin",
                    "LOGIN",
                    "SUCCESS",
                    "LOW",
                    "SOC Administrator authenticated via 2FA Web Console.",
                ),
                # Distributed Brute Force Attempt (5 failed attempts from rogue IP)
                (
                    (now - timedelta(minutes=45)).isoformat(),
                    "198.51.100.75",
                    "root",
                    "SSH_LOGIN",
                    "FAILED",
                    "HIGH",
                    "Invalid root SSH private key authentication attempt 1.",
                ),
                (
                    (now - timedelta(minutes=44)).isoformat(),
                    "198.51.100.75",
                    "root",
                    "SSH_LOGIN",
                    "FAILED",
                    "HIGH",
                    "Invalid root SSH password attempt 2.",
                ),
                (
                    (now - timedelta(minutes=43)).isoformat(),
                    "198.51.100.75",
                    "root",
                    "SSH_LOGIN",
                    "FAILED",
                    "HIGH",
                    "Invalid root SSH password attempt 3.",
                ),
                (
                    (now - timedelta(minutes=42)).isoformat(),
                    "198.51.100.75",
                    "root",
                    "SSH_LOGIN",
                    "FAILED",
                    "HIGH",
                    "Invalid root SSH password attempt 4.",
                ),
                (
                    (now - timedelta(minutes=41)).isoformat(),
                    "198.51.100.75",
                    "root",
                    "SSH_LOGIN",
                    "FAILED",
                    "HIGH",
                    "Invalid root SSH password attempt 5 - Brute force threshold exceeded.",
                ),
                # SQL Injection Attempt
                (
                    (now - timedelta(minutes=35)).isoformat(),
                    "203.0.113.104",
                    "anonymous",
                    "SQL_INJECTION",
                    "BLOCKED",
                    "CRITICAL",
                    "WAF Rule #942100 triggered: Union-based SQL injection detected on '/api/v1/users?id=1 UNION SELECT null,password_hash FROM admin_users'.",
                ),
                # Lateral Movement / Recon Port Scan
                (
                    (now - timedelta(minutes=28)).isoformat(),
                    "203.0.113.88",
                    "unknown",
                    "PORT_SCAN",
                    "BLOCKED",
                    "HIGH",
                    "SYN stealth port sweep blocked across ports 21, 22, 80, 443, 3389, 5432.",
                ),
                # Unauthorized Privilege Escalation Attempt
                (
                    (now - timedelta(minutes=20)).isoformat(),
                    "10.0.0.64",
                    "intern_guest",
                    "PRIVILEGE_ESCALATION",
                    "FAILED",
                    "CRITICAL",
                    "Unauthorized attempt to execute '/usr/bin/sudo -l' without sudoers entry.",
                ),
                # Legitimate File Access
                (
                    (now - timedelta(minutes=15)).isoformat(),
                    "192.168.1.18",
                    "sarah_analyst",
                    "FILE_ACCESS",
                    "SUCCESS",
                    "LOW",
                    "Downloaded quarterly compliance audit log: 'audit_2026_q3.enc'.",
                ),
                # Ransomware Canary File Tripwire
                (
                    (now - timedelta(minutes=8)).isoformat(),
                    "10.0.0.112",
                    "dev_workstation",
                    "FILE_MODIFICATION",
                    "BLOCKED",
                    "CRITICAL",
                    "Tripwire honeypot file 'confidential_payroll.xlsx.lock' modified in rapid succession.",
                ),
                # Password Reset Activity
                (
                    (now - timedelta(minutes=2)).isoformat(),
                    "192.168.1.25",
                    "michael_ops",
                    "PASSWORD_RESET",
                    "SUCCESS",
                    "MEDIUM",
                    "Self-service password reset confirmed via email token verification.",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO security_events
                (event_time, source_ip, username, event_type, status, severity, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                events,
            )

            # Generate initial alerts for critical and brute force events
            cursor.execute("SELECT id FROM security_events WHERE event_type = 'SQL_INJECTION' LIMIT 1")
            sql_row = cursor.fetchone()
            if sql_row:
                cursor.execute(
                    """
                    INSERT INTO security_alerts (event_id, alert_type, severity, message, alert_status)
                    VALUES (?, 'SQL_INJECTION_ALERT', 'CRITICAL', ?, 'OPEN')
                    """,
                    (sql_row[0], "Active WAF blockage: Union SQLi payload from IP 203.0.113.104"),
                )

            cursor.execute("SELECT id FROM security_events WHERE event_type = 'PRIVILEGE_ESCALATION' LIMIT 1")
            priv_row = cursor.fetchone()
            if priv_row:
                cursor.execute(
                    """
                    INSERT INTO security_alerts (event_id, alert_type, severity, message, alert_status)
                    VALUES (?, 'PRIVILEGE_ESCALATION_ALERT', 'CRITICAL', ?, 'OPEN')
                    """,
                    (priv_row[0], "Unauthorized sudo execution attempted by user 'intern_guest'"),
                )

            logger.info("Seeded %d realistic cybersecurity events and associated alerts.", len(events))

    except sqlite3.Error as error:
        logger.error("Failed to seed sample cybersecurity data: %s", error)


if __name__ == "__main__":
    if initialize_database():
        seed_sample_data(force=False)
