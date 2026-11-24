/**
 * Enterprise Cybersecurity SOC Dashboard Client Controllers
 * File: static/script.js
 */

// 1. Toast Notification Utility
function showToast(message, type = "info", duration = 4000) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "❌";

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// 2. Real-Time Security Log Multi-Filter
function filterSecurityLogs() {
    const searchVal = (document.getElementById("logSearch")?.value || "").toLowerCase().trim();
    const severityVal = (document.getElementById("severityFilter")?.value || "").toUpperCase().trim();
    const statusVal = (document.getElementById("statusFilter")?.value || "").toUpperCase().trim();

    const table = document.getElementById("securityLogsTable");
    if (!table) return;

    const rows = table.getElementsByClassName("log-row");

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const rowText = row.textContent.toLowerCase();
        const rowSev = (row.getAttribute("data-severity") || "").toUpperCase();
        const rowStat = (row.getAttribute("data-status") || "").toUpperCase();

        const matchesSearch = !searchVal || rowText.includes(searchVal);
        const matchesSeverity = !severityVal || rowSev === severityVal;
        const matchesStatus = !statusVal || rowStat === statusVal;

        if (matchesSearch && matchesSeverity && matchesStatus) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    }
}

function clearLogSearch() {
    const sInput = document.getElementById("logSearch");
    const sevFilter = document.getElementById("severityFilter");
    const statFilter = document.getElementById("statusFilter");

    if (sInput) sInput.value = "";
    if (sevFilter) sevFilter.value = "";
    if (statFilter) statFilter.value = "";

    filterSecurityLogs();
}

// Compatibility alias
function searchSecurityLogs() {
    filterSecurityLogs();
}

// 3. Resolve Single Security Incident via AJAX
async function resolveAlertAjax(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/resolve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ analyst: "SOC_ANALYST" })
        });
        const result = await response.json();

        if (result.status === "success") {
            const statusBadge = document.getElementById(`status-badge-${alertId}`);
            if (statusBadge) {
                statusBadge.textContent = "RESOLVED";
                statusBadge.className = "status-badge resolved";
            }

            const row = document.getElementById(`alert-row-${alertId}`);
            if (row) {
                const actionCell = row.cells[row.cells.length - 1];
                actionCell.innerHTML = `<span class="badge-closed">Closed</span>`;
            }

            const countElem = document.getElementById("openAlertCount");
            if (countElem) {
                const cur = parseInt(countElem.textContent) || 0;
                countElem.textContent = Math.max(0, cur - 1);
            }

            showToast(`Incident #${alertId} marked as RESOLVED.`, "success");
        } else {
            showToast(`Error: ${result.message || "Failed to resolve alert."}`, "error");
        }
    } catch (err) {
        console.error("Resolve Alert Error:", err);
        showToast("Network error while resolving incident.", "error");
    }
}

// 4. Batch Resolve All Open Alerts
async function resolveAllAlertsAjax() {
    if (!confirm("Confirm resolution of ALL open security alerts?")) return;

    try {
        const response = await fetch("/api/alerts/resolve-all", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const result = await response.json();

        if (result.status === "success") {
            showToast(result.message, "success");
            setTimeout(() => location.reload(), 800);
        } else {
            showToast("Failed to batch resolve alerts.", "error");
        }
    } catch (err) {
        console.error("Batch Resolve Error:", err);
        showToast("Network failure executing batch resolution.", "error");
    }
}

// 5. Trigger Real-Time Threat Correlation Scanner
async function triggerThreatScan() {
    showToast("Executing multi-vector threat correlation scan...", "info", 2000);

    try {
        const response = await fetch("/api/threats/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const result = await response.json();

        if (result.status === "success") {
            const data = result.data || {};
            const total = data.total_threats_found || 0;
            const newAlerts = data.new_alerts_generated || 0;

            showToast(`Scan complete: ${total} threats correlated, ${newAlerts} new alerts generated.`, "success");
            setTimeout(() => location.reload(), 1200);
        } else {
            showToast("Threat correlation scan returned an error.", "error");
        }
    } catch (err) {
        console.error("Threat Scan Error:", err);
        showToast("Network error contacting threat engine.", "error");
    }
}

// 6. Modal Controllers for Ingesting Logs
function openNewLogModal() {
    const modal = document.getElementById("newLogModal");
    if (modal) modal.style.display = "flex";
}

function closeNewLogModal() {
    const modal = document.getElementById("newLogModal");
    if (modal) modal.style.display = "none";
}

window.addEventListener("click", (e) => {
    const modal = document.getElementById("newLogModal");
    if (e.target === modal) {
        closeNewLogModal();
    }
});

// 7. Submit Ingested Security Log
async function submitNewLog(event) {
    event.preventDefault();

    const payload = {
        source_ip: document.getElementById("modalSourceIp").value,
        username: document.getElementById("modalUsername").value,
        event_type: document.getElementById("modalEventType").value,
        status: document.getElementById("modalStatus").value,
        severity: document.getElementById("modalSeverity").value,
        details: document.getElementById("modalDetails").value
    };

    try {
        const response = await fetch("/api/logs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.status === "success") {
            closeNewLogModal();
            showToast("Security event ingested successfully!", "success");
            setTimeout(() => location.reload(), 700);
        } else {
            showToast(`Failed to record log: ${result.message}`, "error");
        }
    } catch (err) {
        console.error("Submit Log Error:", err);
        showToast("Network error recording log event.", "error");
    }
}

// 8. Navigation Active State
function setActiveNav(element) {
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    if (element) element.classList.add("active");
}

// 8. Navigation Active State
function setActiveNav(element) {
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    if (element) element.classList.add("active");
}

