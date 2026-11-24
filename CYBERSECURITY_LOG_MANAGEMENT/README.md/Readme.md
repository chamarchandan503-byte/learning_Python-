# 🛡️ Enterprise Cybersecurity Log Management & SIEM Defense System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-black.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![SIEM](https://img.shields.io/badge/Architecture-SOC%20SIEM-red.svg)](#)

---

## 📌 Executive Overview
The **Enterprise Cybersecurity Log Management System** is a production-grade Security Information and Event Management (SIEM) and Security Operations Center (SOC) framework. Built with Python and Flask, it ingests, sanitizes, analyzes, and correlates security telemetry in real-time. It equips security analysts with the tools needed to detect distributed brute-force attacks, web injections (SQLi, XSS), port scans, privilege escalations, and audit compliance violations.

---

## ✨ Key Enterprise Capabilities

1. **Centralized Security Telemetry Ingestion**:
   - Ingests authentication logs, SSH logins, database queries, file access logs, and firewall drop rules.
   - Comprehensive sanitization protecting against log forging and **CRLF injection** attacks.
   - IPv4 regex validation and ISO-8601 UTC timestamp standardization.

2. **Automated Multi-Vector Threat Correlation**:
   - **Brute Force Detection**: Correlates authentication failures ($\ge 5$ failed attempts) per IP and targeted user.
   - **Web Attacks (WAF)**: Detects SQL Injections, Command Injections, and XSS patterns.
   - **Reconnaissance Sweeps**: Detects stealth SYN port scans and network sweeps.
   - **Duplicate Alert Suppression**: Avoids spamming analysts with repetitive alerts for active ongoing threats.

3. **SOC Incident Triage & Response Workflow**:
   - Real-time incident lifecycle management (`OPEN` $\rightarrow$ `RESOLVED`).
   - One-click AJAX incident resolution directly from the SOC web dashboard.
   - Interactive terminal CLI (`modules/alert_manager.py`) for command-line security operators.

4. **Threat Intelligence & Risk Economics**:
   - Aggregates severity distribution (Critical, High, Medium, Low) and operation statuses (Success, Failed, Blocked).
   - Dynamic **Security Posture Score (0-100%)** reflecting real-time organizational threat posture.
   - Quantified breach cost modeling and automated threat mitigation ROI calculator (`modules/profit_analysis.py`).

5. **Modern Dark-Mode SOC Portal**:
   - High-contrast, futuristic dark theme designed for 24/7 security analyst operations.
   - Real-time client-side multi-filter (Instant search + Severity dropdown + Status dropdown).
   - Ingest Event modal dialog for manual telemetry injection.
   - RFC-4180 compliant CSV audit log streaming export (`/api/export/csv`).

---

## 🏗️ Architectural Topology

```text
CYBERSECURITY_LOG_MANAGEMENT/
├── app.py                      # Flask SOC Web Application & RESTful API
├── database.py                 # SQLite WAL connection manager & sample seeder
├── requirements.txt            # Production dependencies
├── requirment.txt             # Dependency alias
├── cybersecurity.db            # Persistent SQLite database
│
├── Database/
│   └── schema.sql              # Relational schema (Events, Alerts, Users, Audit, Indexes)
│
├── modules/
│   ├── log_collector.py        # Ingestion engine & attack simulation utilities
│   ├── threat_detector.py      # Automated SIEM threat correlation scanner
│   ├── alert_manager.py        # Incident triage, resolution, and CLI console
│   ├── log_analyzer.py         # Statistical analytics, posture scoring & CSV export
│   └── profit_analysis.py      # Financial risk exposure & mitigation ROI calculator
│
├── Data/
│   ├── sample_security_logs.csv# Realistic attack & authorized telemetry dataset
│   └── modules/
│       └── data_cleaning.py    # Sanitization, normalization & batch CSV ingestor
│
├── templates/
│   └── index.html              # Dark-mode SOC dashboard template
│
└── static/
    ├── style.css               # Theme stylesheet
    ├── script.js               # Client controllers, live search & AJAX handlers
    ├── css/
    │   └── style.css           # Path alias
    └── js/
        └── dashboard.js        # Path alias
```

---

## 🗄️ Database Schema Specification

### 1. `security_events` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique event identifier |
| `event_time` | TEXT | NOT NULL | ISO 8601 UTC timestamp |
| `source_ip` | TEXT | NOT NULL | Client / source IPv4 address |
| `username` | TEXT | DEFAULT 'anonymous' | Target account or operator username |
| `event_type` | TEXT | NOT NULL | LOGIN, SSH_LOGIN, SQL_INJECTION, PORT_SCAN, etc. |
| `status` | TEXT | CHECK IN ('SUCCESS','FAILED','BLOCKED') | Operation outcome |
| `severity` | TEXT | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL')| Risk rating |
| `details` | TEXT | - | Payload details, audit messages |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | Ingestion timestamp |

### 2. `security_alerts` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique alert ID |
| `event_id` | INTEGER | FOREIGN KEY REFERENCES security_events | Associated triggering event |
| `alert_type` | TEXT | NOT NULL | BRUTE_FORCE, SQL_INJECTION_ALERT, etc. |
| `severity` | TEXT | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL')| Threat severity |
| `message` | TEXT | NOT NULL | Analyst actionable description |
| `alert_status`| TEXT | CHECK IN ('OPEN','RESOLVED','DISMISSED') | Incident lifecycle state |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | Incident creation timestamp |
| `resolved_at`| TEXT | - | Resolution timestamp |
| `resolved_by`| TEXT | - | Analyst username who closed the alert |

---

## 🔌 RESTful API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Primary SOC Interactive Web Portal |
| `GET` | `/api/stats` | System telemetry, posture score, and alert breakdown |
| `GET` | `/api/logs` | Query logs (`?severity=&status=&search=&limit=`) |
| `POST` | `/api/logs` | Ingest new event telemetry (`JSON payload`) |
| `GET` | `/api/alerts` | Query active incidents (`?status=OPEN`) |
| `POST` | `/api/alerts/<id>/resolve` | Resolve single incident alert via AJAX |
| `POST` | `/api/alerts/resolve-all` | Batch-resolve all currently open alerts |
| `POST` | `/api/threats/scan` | Execute real-time threat correlation scanner |
| `GET` | `/api/export/csv` | Download complete security events as CSV |

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
cd c:\Users\ChandanRao\Desktop\python\CYBERSECURITY_LOG_MANAGEMENT
pip install -r requirements.txt
```

### 2. Database Initialization & Seeding
```bash
python database.py
```

### 3. Launch the SOC Web Portal
```bash
python app.py
```
Open your web browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🛠️ CLI Operations (Module Testing)

- **Execute Threat Correlation Engine**:
  ```bash
  python modules/threat_detector.py
  ```
- **Launch Interactive Alert Management Console**:
  ```bash
  python modules/alert_manager.py
  ```
- **Generate SIEM Telemetry & Posture Briefing**:
  ```bash
  python modules/log_analyzer.py
  ```
- **Simulate Attack Scenarios**:
  ```bash
  python modules/log_collector.py
  ```
- **Calculate Financial Risk & Mitigation ROI**:
  ```bash
  python modules/profit_analysis.py
  ```
- **Clean & Ingest Raw CSV Logs**:
  ```bash
  python Data/modules/data_cleaning.py
  ```
