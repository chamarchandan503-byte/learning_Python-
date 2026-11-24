"""Enterprise Cybersecurity Log Management System - Flask Web Application & SOC Portal

File: app.py
Description: Production-ready SIEM web dashboard and RESTful API facilitating real-time
             log surveillance, threat correlation, incident triage, and audit exports.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Tuple
from flask import Flask, render_template, request, jsonify, Response

# Module imports
from database import initialize_database, seed_sample_data, get_connection
from modules.log_collector import collect_log
from modules.threat_detector import detect_all_threats
from modules.alert_manager import resolve_alert, resolve_all_alerts, get_alerts, get_alert_metrics
from modules.log_analyzer import analyze_logs, get_all_logs

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [SOC-App] %(message)s")
logger = logging.getLogger("SOC-App")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "cybersecurity.db"


@app.after_request
def apply_security_headers(response):
    """Add defensive security headers to all HTTP responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


def get_dashboard_payload() -> Tuple[Dict[str, Any], int, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Compile aggregated metrics, active alerts, and latest logs for UI rendering."""
    analytics = analyze_logs()
    alert_metrics = get_alert_metrics()
    latest_logs = get_all_logs(limit=30)
    latest_alerts = get_alerts(limit=20)

    stats = {
        "total_events": analytics["total_events"],
        "failed_logins": analytics["failed_logins"],
        "high_risk_events": analytics["severity_distribution"]["CRITICAL"] + analytics["severity_distribution"]["HIGH"],
        "blocked_events": analytics["blocked_events"],
        "security_score": analytics["security_posture_score"],
        "threat_level": analytics["threat_level"],
        "severity_distribution": analytics["severity_distribution"],
    }

    return stats, alert_metrics["open_alerts"], latest_logs, latest_alerts


# ==============================================================================
# WEB DASHBOARD ROUTES
# ==============================================================================

@app.route("/")
def dashboard():
    """Main Security Operations Center (SOC) interactive portal."""
    stats, open_alert_count, logs, alerts = get_dashboard_payload()
    return render_template(
        "index.html",
        stats=stats,
        alert_count=open_alert_count,
        logs=logs,
        alerts=alerts,
        current_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )


# ==============================================================================
# RESTFUL API ENDPOINTS
# ==============================================================================

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return complete SIEM system metrics in JSON format."""
    data = analyze_logs()
    alert_metrics = get_alert_metrics()
    return jsonify({
        "status": "success",
        "data": {
            "analytics": data,
            "alerts": alert_metrics
        }
    }), 200


@app.route("/api/logs", methods=["GET"])
def api_get_logs():
    """Query security events with multi-criteria filtering."""
    limit = int(request.args.get("limit", 100))
    severity = request.args.get("severity")
    status = request.args.get("status")
    event_type = request.args.get("event_type")
    search = request.args.get("search")

    logs = get_all_logs(
        limit=limit,
        severity=severity,
        status=status,
        event_type=event_type,
        search_keyword=search
    )
    return jsonify({
        "status": "success",
        "count": len(logs),
        "data": logs
    }), 200


@app.route("/api/logs", methods=["POST"])
def api_ingest_log():
    """Ingest a new security event telemetry record."""
    payload = request.get_json(silent=True) or request.form

    source_ip = str(payload.get("source_ip", "")).strip()
    username = str(payload.get("username", "")).strip() or "anonymous"
    event_type = str(payload.get("event_type", "")).strip()
    status = str(payload.get("status", "")).strip().upper()
    severity = str(payload.get("severity", "")).strip().upper()
    details = str(payload.get("details", "")).strip()

    if not source_ip or not event_type or not status or not severity:
        return jsonify({
            "status": "error",
            "message": "Missing required fields: source_ip, event_type, status, severity."
        }), 400

    event_id = collect_log(
        source_ip=source_ip,
        username=username,
        event_type=event_type,
        status=status,
        severity=severity,
        details=details
    )

    if event_id:
        return jsonify({
            "status": "success",
            "message": "Security event recorded successfully.",
            "event_id": event_id
        }), 201
    else:
        return jsonify({
            "status": "error",
            "message": "Validation failed: Invalid status or severity value."
        }), 422


@app.route("/api/alerts", methods=["GET"])
def api_get_alerts():
    """Retrieve security incident alerts."""
    status_filter = request.args.get("status")
    severity_filter = request.args.get("severity")
    limit = int(request.args.get("limit", 50))

    alerts = get_alerts(status_filter=status_filter, severity_filter=severity_filter, limit=limit)
    return jsonify({
        "status": "success",
        "count": len(alerts),
        "data": alerts
    }), 200


@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def api_resolve_single_alert(alert_id):
    """Mark a specific security alert as RESOLVED."""
    payload = request.get_json(silent=True) or {}
    analyst = payload.get("analyst", "SOC_ANALYST")

    success = resolve_alert(alert_id=alert_id, resolved_by=analyst)
    if success:
        return jsonify({
            "status": "success",
            "message": f"Security Alert #{alert_id} has been marked as RESOLVED."
        }), 200
    return jsonify({
        "status": "error",
        "message": f"Alert #{alert_id} not found or already closed."
    }), 404


@app.route("/api/alerts/resolve-all", methods=["POST"])
def api_resolve_all_alerts():
    """Batch-resolve all open security alerts."""
    resolved_count = resolve_all_alerts(resolved_by="SOC_MANAGER")
    return jsonify({
        "status": "success",
        "message": f"Successfully resolved {resolved_count} open incidents.",
        "resolved_count": resolved_count
    }), 200


@app.route("/api/threats/scan", methods=["POST"])
def api_trigger_threat_scan():
    """Trigger the real-time SIEM multi-vector threat correlation engine."""
    scan_report = detect_all_threats()
    return jsonify({
        "status": "success",
        "message": "Threat correlation scan executed successfully.",
        "data": scan_report
    }), 200


@app.route("/api/export/csv", methods=["GET"])
def api_export_csv():
    """Stream all security event logs as an RFC-4180 compliant CSV attachment."""
    logs = get_all_logs(limit=10000)
    if not logs:
        return jsonify({"status": "error", "message": "No security events to export."}), 404

    fieldnames = ["id", "event_time", "source_ip", "username", "event_type", "status", "severity", "details"]

    def generate_csv_stream():
        yield ",".join(fieldnames) + "\n"
        for log in logs:
            row = []
            for field in fieldnames:
                val = str(log.get(field, "")).replace('"', '""')
                row.append(f'"{val}"')
            yield ",".join(row) + "\n"

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"cybersecurity_logs_{timestamp_str}.csv"

    return Response(
        generate_csv_stream(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==============================================================================
# GLOBAL ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "API endpoint not found."}), 404
    return render_template("index.html", error="Page Not Found (404)"), 404


@app.errorhandler(500)
def handle_500(e):
    logger.error("Internal Server Error: %s", e)
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Internal server error occurred."}), 500
    return "Internal Server Error", 500


# ==============================================================================
# APPLICATION ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    # Ensure database tables exist and seed sample events if database is fresh
    initialize_database()
    seed_sample_data(force=False)

    logger.info("Enterprise SOC Dashboard running on http://127.0.0.1:5000")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
