"""Enterprise Cybersecurity Log Management System - Log Analytics & SIEM Telemetry Engine

File: modules/log_analyzer.py
Description: Performs deep statistical analysis on security logs, identifies attack vectors,
             computes enterprise security posture score, and supports audit exports.
"""

import csv
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [LogAnalyzer] %(message)s")
logger = logging.getLogger("LogAnalyzer")

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"


def get_connection(row_factory: bool = True) -> sqlite3.Connection:
    """Return an active SQLite connection."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


def get_all_logs(
    limit: int = 100,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    search_keyword: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve filtered security events with parameterized SQL query protection."""
    conditions = []
    params = []

    if severity:
        conditions.append("severity = ?")
        params.append(severity.upper().strip())

    if status:
        conditions.append("status = ?")
        params.append(status.upper().strip())

    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type.upper().strip())

    if search_keyword:
        kw = f"%{search_keyword.strip()}%"
        conditions.append("(source_ip LIKE ? OR username LIKE ? OR details LIKE ? OR event_type LIKE ?)")
        params.extend([kw, kw, kw, kw])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT id, event_time, source_ip, username, event_type, status, severity, details, created_at
        FROM security_events
        {where_clause}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(limit)

    logs = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            logs = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as err:
        logger.error("Failed to query log events: %s", err)

    return logs


def analyze_logs() -> Dict[str, Any]:
    """Calculate aggregated SIEM security metrics, threat distribution, and posture score."""
    analysis = {
        "total_events": 0,
        "successful_events": 0,
        "failed_events": 0,
        "blocked_events": 0,
        "failed_logins": 0,
        "severity_distribution": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "top_threat_ips": [],
        "top_targeted_users": [],
        "top_event_types": [],
        "open_incidents": 0,
        "security_posture_score": 100,
        "threat_level": "NORMAL",
    }

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. High-level aggregates
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_count,
                    SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked_count,
                    SUM(CASE WHEN event_type IN ('LOGIN', 'SSH_LOGIN', 'AUTH') AND status = 'FAILED' THEN 1 ELSE 0 END) as failed_auths,
                    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as crit_count,
                    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_count,
                    SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) as med_count,
                    SUM(CASE WHEN severity = 'LOW' THEN 1 ELSE 0 END) as low_count
                FROM security_events
                """
            )
            r = cursor.fetchone()
            if r:
                analysis["total_events"] = r["total"] or 0
                analysis["successful_events"] = r["success_count"] or 0
                analysis["failed_events"] = r["failed_count"] or 0
                analysis["blocked_events"] = r["blocked_count"] or 0
                analysis["failed_logins"] = r["failed_auths"] or 0
                analysis["severity_distribution"]["CRITICAL"] = r["crit_count"] or 0
                analysis["severity_distribution"]["HIGH"] = r["high_count"] or 0
                analysis["severity_distribution"]["MEDIUM"] = r["med_count"] or 0
                analysis["severity_distribution"]["LOW"] = r["low_count"] or 0

            # 2. Count active unresolved alerts
            cursor.execute("SELECT COUNT(*) as open_cnt FROM security_alerts WHERE alert_status = 'OPEN'")
            open_row = cursor.fetchone()
            analysis["open_incidents"] = open_row["open_cnt"] if open_row else 0

            # 3. Top offending source IP addresses
            cursor.execute(
                """
                SELECT source_ip,
                       COUNT(*) as total_requests,
                       SUM(CASE WHEN status IN ('FAILED', 'BLOCKED') THEN 1 ELSE 0 END) as threat_hits
                FROM security_events
                GROUP BY source_ip
                ORDER BY threat_hits DESC, total_requests DESC
                LIMIT 5
                """
            )
            analysis["top_threat_ips"] = [dict(row) for row in cursor.fetchall()]

            # 4. Top targeted user accounts
            cursor.execute(
                """
                SELECT username, COUNT(*) as hit_count
                FROM security_events
                WHERE username IS NOT NULL AND username != ''
                GROUP BY username
                ORDER BY hit_count DESC
                LIMIT 5
                """
            )
            analysis["top_targeted_users"] = [dict(row) for row in cursor.fetchall()]

            # 5. Top event types breakdown
            cursor.execute(
                """
                SELECT event_type, COUNT(*) as volume
                FROM security_events
                GROUP BY event_type
                ORDER BY volume DESC
                LIMIT 6
                """
            )
            analysis["top_event_types"] = [dict(row) for row in cursor.fetchall()]

            # 6. Enterprise Security Posture Index (0 - 100)
            score = 100
            score -= analysis["open_incidents"] * 12
            score -= analysis["severity_distribution"]["CRITICAL"] * 8
            score -= analysis["severity_distribution"]["HIGH"] * 4
            score -= analysis["failed_logins"] * 2
            final_score = max(5, min(100, score))
            analysis["security_posture_score"] = final_score

            if final_score < 40:
                analysis["threat_level"] = "CRITICAL_DEFENSE"
            elif final_score < 70:
                analysis["threat_level"] = "ELEVATED_RISK"
            elif final_score < 90:
                analysis["threat_level"] = "MODERATE_WARNING"
            else:
                analysis["threat_level"] = "NORMAL_HEALTHY"

    except sqlite3.Error as err:
        logger.error("Log analysis calculation error: %s", err)

    return analysis


def print_siem_report():
    """Print complete formatted SOC intelligence briefing to the terminal."""
    a = analyze_logs()
    print("\n" + "=" * 65)
    print("      ENTERPRISE SIEM THREAT & LOG INTELLIGENCE REPORT      ")
    print("=" * 65)
    print(f"Total Telemetry Events : {a['total_events']}")
    print(f"Successful Operations  : {a['successful_events']}")
    print(f"Failed Operations      : {a['failed_events']}")
    print(f"Blocked Mitigations    : {a['blocked_events']}")
    print(f"Failed Authentication  : {a['failed_logins']}")
    print("-" * 65)
    print("Severity Profile:")
    for sev, cnt in a["severity_distribution"].items():
        print(f"  [{sev:<8}] : {cnt}")
    print("-" * 65)
    print(f"Unresolved Incidents   : {a['open_incidents']}")
    print(f"Security Posture Score : {a['security_posture_score']}/100 [{a['threat_level']}]")
    print("=" * 65)

    if a["top_threat_ips"]:
        print("\nTop 5 Offending Source IPs:")
        for idx, ip_data in enumerate(a["top_threat_ips"], start=1):
            print(f"  {idx}. {ip_data['source_ip']:<15} (Threat Hits: {ip_data['threat_hits']}, Total: {ip_data['total_requests']})")

    if a["top_targeted_users"]:
        print("\nTop Targeted User Accounts:")
        for idx, u in enumerate(a["top_targeted_users"], start=1):
            print(f"  {idx}. {u['username']:<15} (Events: {u['hit_count']})")
    print("=" * 65 + "\n")


def export_logs_to_csv(filepath: Optional[str] = None) -> Optional[str]:
    """Export all security logs to a clean CSV report."""
    logs = get_all_logs(limit=10000)
    if not logs:
        logger.warning("No logs available for export.")
        return None

    target = Path(filepath) if filepath else (BASE_DIR / "security_events_export.csv")
    try:
        fields = ["id", "event_time", "source_ip", "username", "event_type", "status", "severity", "details"]
        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(logs)
        logger.info("Exported %d logs to %s", len(logs), target)
        return str(target)
    except OSError as err:
        logger.error("CSV export failed: %s", err)
        return None


if __name__ == "__main__":
    print_siem_report()
