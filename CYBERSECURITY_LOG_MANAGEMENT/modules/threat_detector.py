"""Enterprise Cybersecurity Log Management System - Threat Detection & Correlation Engine

File: modules/threat_detector.py
Description: Scans telemetry for multi-vector threat patterns including Brute Force attacks,
             Web Injections (SQLi/XSS), Reconnaissance sweeps, and Privilege Escalations.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ThreatDetector] %(message)s")
logger = logging.getLogger("ThreatDetector")

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"

# Detection parameters
BRUTE_FORCE_THRESHOLD = 5
PORT_SCAN_THRESHOLD = 3


def get_connection() -> sqlite3.Connection:
    """Return an SQLite connection."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def detect_brute_force_attacks(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """Identify sources exceeding repeated authentication failures."""
    detected = []
    cursor.execute(
        """
        SELECT source_ip, username, COUNT(*) as failed_attempts
        FROM security_events
        WHERE event_type IN ('LOGIN', 'SSH_LOGIN', 'AUTH')
          AND status = 'FAILED'
        GROUP BY source_ip, username
        HAVING COUNT(*) >= ?
        """,
        (BRUTE_FORCE_THRESHOLD,),
    )
    rows = cursor.fetchall()

    for ip, user, count in rows:
        # Retrieve latest event ID for alert association
        cursor.execute(
            """
            SELECT id FROM security_events
            WHERE source_ip = ? AND username = ? AND status = 'FAILED'
            ORDER BY id DESC LIMIT 1
            """,
            (ip, user),
        )
        latest_event = cursor.fetchone()
        event_id = latest_event[0] if latest_event else None

        # Check for pre-existing OPEN alert for this target/source
        cursor.execute(
            """
            SELECT id FROM security_alerts
            WHERE alert_type = 'BRUTE_FORCE'
              AND alert_status = 'OPEN'
              AND message LIKE ?
            """,
            (f"%{ip}%",),
        )
        existing_alert = cursor.fetchone()

        if not existing_alert and event_id:
            alert_msg = f"Brute Force Alert: {count} failed logins observed for user '{user}' from IP {ip}"
            cursor.execute(
                """
                INSERT INTO security_alerts (event_id, alert_type, severity, message, alert_status)
                VALUES (?, 'BRUTE_FORCE', 'HIGH', ?, 'OPEN')
                """,
                (event_id, alert_msg),
            )
            detected.append(
                {
                    "vector": "BRUTE_FORCE",
                    "severity": "HIGH",
                    "source_ip": ip,
                    "target_user": user,
                    "event_count": count,
                    "status": "NEW_ALERT_CREATED",
                    "message": alert_msg,
                }
            )
            logger.warning("New Brute Force Alert generated for IP: %s (User: %s)", ip, user)
        else:
            detected.append(
                {
                    "vector": "BRUTE_FORCE",
                    "severity": "HIGH",
                    "source_ip": ip,
                    "target_user": user,
                    "event_count": count,
                    "status": "ALERT_ALREADY_ACTIVE",
                    "message": f"Ongoing threat: Active alert exists for {ip}",
                }
            )

    return detected


def detect_web_and_injection_threats(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """Identify SQLi, XSS, and command injection attacks."""
    detected = []
    cursor.execute(
        """
        SELECT id, source_ip, username, event_type, severity, details
        FROM security_events
        WHERE event_type IN ('SQL_INJECTION', 'XSS', 'PATH_TRAVERSAL', 'COMMAND_INJECTION')
           OR severity = 'CRITICAL'
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()

    for event_id, ip, user, event_type, sev, details in rows:
        cursor.execute(
            """
            SELECT id FROM security_alerts
            WHERE event_id = ? AND alert_status = 'OPEN'
            """,
            (event_id,),
        )
        existing = cursor.fetchone()

        if not existing:
            alert_msg = f"Critical {event_type} breach attempt by '{user}' from IP {ip}: {details[:120]}"
            cursor.execute(
                """
                INSERT INTO security_alerts (event_id, alert_type, severity, message, alert_status)
                VALUES (?, ?, 'CRITICAL', ?, 'OPEN')
                """,
                (event_id, f"{event_type}_ALERT", alert_msg),
            )
            detected.append(
                {
                    "vector": event_type,
                    "severity": "CRITICAL",
                    "source_ip": ip,
                    "target_user": user,
                    "status": "NEW_ALERT_CREATED",
                    "message": alert_msg,
                }
            )
            logger.critical("Critical Threat Flagged: %s from IP %s", event_type, ip)

    return detected


def detect_reconnaissance_sweeps(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """Identify port scans and network sweep probes."""
    detected = []
    cursor.execute(
        """
        SELECT source_ip, COUNT(*) as sweep_count
        FROM security_events
        WHERE event_type IN ('PORT_SCAN', 'NETWORK_SWEEP', 'PROBE')
        GROUP BY source_ip
        HAVING COUNT(*) >= ?
        """,
        (PORT_SCAN_THRESHOLD,),
    )
    rows = cursor.fetchall()

    for ip, count in rows:
        cursor.execute(
            """
            SELECT id FROM security_alerts
            WHERE alert_type = 'PORT_SCAN_ALERT'
              AND alert_status = 'OPEN'
              AND message LIKE ?
            """,
            (f"%{ip}%",),
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                SELECT id FROM security_events
                WHERE source_ip = ? AND event_type IN ('PORT_SCAN', 'NETWORK_SWEEP', 'PROBE')
                ORDER BY id DESC LIMIT 1
                """,
                (ip,),
            )
            latest = cursor.fetchone()
            event_id = latest[0] if latest else None
            msg = f"Reconnaissance Alert: {count} scanning probes detected from source IP {ip}"

            cursor.execute(
                """
                INSERT INTO security_alerts (event_id, alert_type, severity, message, alert_status)
                VALUES (?, 'PORT_SCAN_ALERT', 'HIGH', ?, 'OPEN')
                """,
                (event_id, msg),
            )
            detected.append(
                {
                    "vector": "PORT_SCAN",
                    "severity": "HIGH",
                    "source_ip": ip,
                    "event_count": count,
                    "status": "NEW_ALERT_CREATED",
                    "message": msg,
                }
            )
            logger.warning("Port scan threat flagged for IP: %s", ip)

    return detected


def detect_all_threats() -> Dict[str, Any]:
    """Execute complete SIEM threat correlation scan and commit newly generated alerts."""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brute_force_threats": [],
        "injection_threats": [],
        "reconnaissance_threats": [],
        "total_threats_found": 0,
        "new_alerts_generated": 0,
    }

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            bf = detect_brute_force_attacks(cursor)
            inj = detect_web_and_injection_threats(cursor)
            recon = detect_reconnaissance_sweeps(cursor)
            conn.commit()

            results["brute_force_threats"] = bf
            results["injection_threats"] = inj
            results["reconnaissance_threats"] = recon

            total_found = len(bf) + len(inj) + len(recon)
            new_alerts = (
                sum(1 for t in bf if t.get("status") == "NEW_ALERT_CREATED")
                + sum(1 for t in inj if t.get("status") == "NEW_ALERT_CREATED")
                + sum(1 for t in recon if t.get("status") == "NEW_ALERT_CREATED")
            )

            results["total_threats_found"] = total_found
            results["new_alerts_generated"] = new_alerts

            logger.info("Threat scan complete. Correlated threats: %d | New alerts: %d", total_found, new_alerts)

    except sqlite3.Error as err:
        logger.error("Threat correlation failed: %s", err)

    return results


if __name__ == "__main__":
    scan_results = detect_all_threats()
    print("\n--- SIEM THREAT CORRELATION REPORT ---")
    print(f"Timestamp: {scan_results['timestamp']}")
    print(f"Total Correlated Threats : {scan_results['total_threats_found']}")
    print(f"New Incidents Created   : {scan_results['new_alerts_generated']}")
    print("---------------------------------------")
