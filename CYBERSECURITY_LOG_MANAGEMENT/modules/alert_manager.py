"""Enterprise Cybersecurity Log Management System - Incident & Alert Management Module

File: modules/alert_manager.py
Description: Provides SOC analysts with tooling to triage, investigate, resolve,
             and dismiss correlated security incident alerts.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [AlertManager] %(message)s")
logger = logging.getLogger("AlertManager")

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"


def get_connection(row_factory: bool = True) -> sqlite3.Connection:
    """Return an active SQLite connection."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


def get_alerts(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve security incident alerts with optional status/severity filtering."""
    conditions = []
    params = []

    if status_filter:
        conditions.append("alert_status = ?")
        params.append(status_filter.upper())

    if severity_filter:
        conditions.append("severity = ?")
        params.append(severity_filter.upper())

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT id, event_id, alert_type, severity, message, alert_status,
               created_at, resolved_at, resolved_by
        FROM security_alerts
        {where_clause}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(limit)

    alerts = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            alerts = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as err:
        logger.error("Failed to query alerts: %s", err)

    return alerts


def resolve_alert(alert_id: int, resolved_by: str = "SOC_ANALYST") -> bool:
    """Mark an active security alert as RESOLVED with audit metadata."""
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with get_connection(row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE security_alerts
                SET alert_status = 'RESOLVED',
                    resolved_at = ?,
                    resolved_by = ?
                WHERE id = ? AND alert_status = 'OPEN'
                """,
                (now_iso, resolved_by, alert_id),
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info("Alert #%d marked as RESOLVED by %s", alert_id, resolved_by)
                return True
            else:
                logger.warning("Alert #%d not found or already closed.", alert_id)
                return False
    except sqlite3.Error as err:
        logger.error("Failed to resolve alert: %s", err)
        return False


def resolve_all_alerts(resolved_by: str = "SOC_ADMIN") -> int:
    """Batch-resolve all open security alerts."""
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with get_connection(row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE security_alerts
                SET alert_status = 'RESOLVED',
                    resolved_at = ?,
                    resolved_by = ?
                WHERE alert_status = 'OPEN'
                """,
                (now_iso, resolved_by),
            )
            conn.commit()
            count = cursor.rowcount
            logger.info("Batch-resolved %d open alerts by %s", count, resolved_by)
            return count
    except sqlite3.Error as err:
        logger.error("Batch alert resolution error: %s", err)
        return 0


def get_alert_metrics() -> Dict[str, Any]:
    """Retrieve statistical distribution of active and historical alerts."""
    metrics = {
        "open_alerts": 0,
        "resolved_alerts": 0,
        "critical_alerts": 0,
        "high_alerts": 0,
        "total_alerts": 0,
    }
    try:
        with get_connection(row_factory=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN alert_status = 'OPEN' THEN 1 ELSE 0 END) as open_cnt,
                    SUM(CASE WHEN alert_status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_cnt,
                    SUM(CASE WHEN severity = 'CRITICAL' AND alert_status = 'OPEN' THEN 1 ELSE 0 END) as crit_cnt,
                    SUM(CASE WHEN severity = 'HIGH' AND alert_status = 'OPEN' THEN 1 ELSE 0 END) as high_cnt
                FROM security_alerts
                """
            )
            row = cursor.fetchone()
            if row:
                metrics["total_alerts"] = row[0] or 0
                metrics["open_alerts"] = row[1] or 0
                metrics["resolved_alerts"] = row[2] or 0
                metrics["critical_alerts"] = row[3] or 0
                metrics["high_alerts"] = row[4] or 0
    except sqlite3.Error as err:
        logger.error("Failed to fetch alert metrics: %s", err)

    return metrics


def display_alerts_terminal(status_filter: Optional[str] = None) -> None:
    """Print security alerts to terminal in a clean tabular view."""
    alerts = get_alerts(status_filter=status_filter)
    title = f"INCIDENT ALERTS [{status_filter or 'ALL'}]"
    print("\n" + "=" * 105)
    print(f" {title.center(103)} ")
    print("=" * 105)
    if not alerts:
        print(" [INFO] No alerts match the selected criteria.")
        print("=" * 105)
        return

    print(f"{'ID':<6} | {'SEVERITY':<10} | {'TYPE':<25} | {'STATUS':<10} | {'TIME':<19} | {'MESSAGE'}")
    print("-" * 105)
    for a in alerts:
        msg = (a.get("message") or "")[:35]
        t = (a.get("created_at") or "")[:19]
        print(f"#{a['id']:<5} | {a['severity']:<10} | {a['alert_type']:<25} | {a['alert_status']:<10} | {t:<19} | {msg}")
    print("=" * 105 + "\n")


def cli_interactive_menu():
    """Command-line operational menu for SOC administrators."""
    while True:
        m = get_alert_metrics()
        print("\n=======================================================")
        print(f"       SIEM ALERT MANAGEMENT CONSOLE")
        print(f"       [Active Incidents: {m['open_alerts']} | Critical: {m['critical_alerts']}]")
        print("=======================================================")
        print(" 1. View All Alerts")
        print(" 2. View Only OPEN Alerts")
        print(" 3. View Only RESOLVED Alerts")
        print(" 4. Resolve an Alert by ID")
        print(" 5. Resolve ALL Open Alerts")
        print(" 6. Exit Console")
        print("-------------------------------------------------------")

        choice = input("Select an option [1-6]: ").strip()
        if choice == "1":
            display_alerts_terminal()
        elif choice == "2":
            display_alerts_terminal(status_filter="OPEN")
        elif choice == "3":
            display_alerts_terminal(status_filter="RESOLVED")
        elif choice == "4":
            try:
                target_id = int(input("Enter Alert ID to mark RESOLVED: "))
                resolve_alert(target_id)
            except ValueError:
                print("[ERROR] Please provide a valid integer ID.")
        elif choice == "5":
            c = input("Confirm resolution of ALL open alerts? (y/N): ").strip().lower()
            if c == "y":
                resolve_all_alerts()
        elif choice == "6":
            print("Exiting SIEM Console.")
            break
        else:
            print("Invalid input. Select between 1 and 6.")


if __name__ == "__main__":
    cli_interactive_menu()
