-- ==============================================================================
-- Enterprise Cybersecurity Log Management & SIEM Defense System
-- Database Schema: SQLite 3.x
-- File: Database/schema.sql
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. Security Event Audit Logs
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    username TEXT DEFAULT 'anonymous',
    event_type TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT (datetime('now', 'utc')),

    CHECK(status IN ('SUCCESS', 'FAILED', 'BLOCKED')),
    CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

-- ------------------------------------------------------------------------------
-- 2. Security Alerts & Incident Responses
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    alert_status TEXT DEFAULT 'OPEN',
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    resolved_at TEXT,
    resolved_by TEXT,

    FOREIGN KEY(event_id) REFERENCES security_events(id) ON DELETE SET NULL,
    CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CHECK(alert_status IN ('OPEN', 'RESOLVED', 'DISMISSED'))
);

-- ------------------------------------------------------------------------------
-- 3. SOC Analyst User Accounts
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'ANALYST',
    created_at TEXT DEFAULT (datetime('now', 'utc')),

    CHECK(role IN ('ADMIN', 'ANALYST', 'AUDITOR'))
);

-- ------------------------------------------------------------------------------
-- 4. Audit Trail for System Activities
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    performed_by TEXT DEFAULT 'SYSTEM',
    timestamp TEXT DEFAULT (datetime('now', 'utc')),
    details TEXT
);

-- ------------------------------------------------------------------------------
-- 5. Performance Indexes
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_events_ip ON security_events(source_ip);
CREATE INDEX IF NOT EXISTS idx_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_events_status ON security_events(status);
CREATE INDEX IF NOT EXISTS idx_events_time ON security_events(event_time);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON security_alerts(alert_status);
CREATE INDEX IF NOT EXISTS idx_alerts_event ON security_alerts(event_id);

-- ------------------------------------------------------------------------------
-- 5. Performance Indexes
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_events_ip ON security_events(source_ip);
CREATE INDEX IF NOT EXISTS idx_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_events_status ON security_events(status);
CREATE INDEX IF NOT EXISTS idx_events_time ON security_events(event_time);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON security_alerts(alert_status);
CREATE INDEX IF NOT EXISTS idx_alerts_event ON security_alerts(event_id);

