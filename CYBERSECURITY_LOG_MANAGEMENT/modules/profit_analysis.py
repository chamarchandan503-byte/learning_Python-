"""Enterprise Cybersecurity Log Management System - Financial Risk & Breach Exposure Analysis

File: modules/profit_analysis.py
Description: Quantifies financial breach risk exposure, incident response costs,
             and returns on investment (ROI) from automated threat mitigations.
"""

import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [RiskAnalysis] %(message)s")
logger = logging.getLogger("RiskAnalysis")

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"

# Industry benchmark breach cost models (in USD $)
BREACH_COST_WEIGHTS = {
    "CRITICAL": 7500.0,  # Data exfiltration, privilege escalation, ransomware tripwires
    "HIGH": 2200.0,      # Automated brute force attacks, credential stuffing, port scans
    "MEDIUM": 450.0,     # Suspicious user anomalous access
    "LOW": 30.0,         # Routine audit compliance check
}


def get_connection() -> sqlite3.Connection:
    """Return an SQLite connection."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def calculate_financial_exposure() -> Dict[str, Any]:
    """Calculate potential breach exposure and mitigated savings from security controls."""
    summary = {
        "gross_financial_exposure": 0.0,
        "mitigated_threat_savings": 0.0,
        "unmitigated_risk_exposure": 0.0,
        "severity_costs": {
            "CRITICAL": 0.0,
            "HIGH": 0.0,
            "MEDIUM": 0.0,
            "LOW": 0.0,
        },
        "event_counts": {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        },
    }

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT severity, status, COUNT(*) as count
                FROM security_events
                GROUP BY severity, status
                """
            )
            rows = cursor.fetchall()

            for severity, status, count in rows:
                unit_cost = BREACH_COST_WEIGHTS.get(severity, 30.0)
                exposure = unit_cost * count

                summary["gross_financial_exposure"] += exposure
                summary["severity_costs"][severity] = summary["severity_costs"].get(severity, 0.0) + exposure
                summary["event_counts"][severity] = summary["event_counts"].get(severity, 0) + count

                if status == "BLOCKED":
                    # Proactively mitigated by firewalls/WAF/SOC controls
                    summary["mitigated_threat_savings"] += exposure
                else:
                    summary["unmitigated_risk_exposure"] += exposure

    except sqlite3.Error as err:
        logger.error("Financial exposure calculation error: %s", err)

    return summary


def calculate_defense_roi(operational_budget: float = 12000.0) -> Dict[str, Any]:
    """Calculate the Return on Investment (ROI) of proactive automated threat mitigation."""
    exposure = calculate_financial_exposure()
    prevented_loss = exposure["mitigated_threat_savings"]

    net_value = prevented_loss - operational_budget
    roi_percent = (net_value / operational_budget) * 100 if operational_budget > 0 else 0.0

    return {
        "operational_budget": operational_budget,
        "prevented_loss": prevented_loss,
        "net_security_value": net_value,
        "roi_percentage": round(roi_percent, 2),
    }


def print_risk_report():
    """Print executive financial risk and mitigation briefing to the terminal."""
    exp = calculate_financial_exposure()
    roi = calculate_defense_roi(operational_budget=15000.0)

    print("\n" + "=" * 65)
    print("      CYBERSECURITY RISK EXPOSURE & MITIGATION ROI REPORT     ")
    print("=" * 65)
    print(f"Gross Threat Financial Exposure : ${exp['gross_financial_exposure']:,.2f}")
    print(f"Loss Prevented (Blocked Attacks): ${exp['mitigated_threat_savings']:,.2f}")
    print(f"Residual Open Risk Exposure     : ${exp['unmitigated_risk_exposure']:,.2f}")
    print("-" * 65)
    print("Exposure By Incident Severity:")
    for sev, val in exp["severity_costs"].items():
        cnt = exp["event_counts"].get(sev, 0)
        print(f"  [{sev:<8}] : ${val:,.2f} ({cnt} events)")
    print("-" * 65)
    print(f"Operational Defense Budget      : ${roi['operational_budget']:,.2f}")
    print(f"Net Security Value Created      : ${roi['net_security_value']:,.2f}")
    print(f"Security Mitigation ROI         : {roi['roi_percentage']}%")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    print_risk_report()
