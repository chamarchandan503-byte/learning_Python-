// Smart E-Commerce Main Scripts

document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    console.log("Smart E-Commerce Management System ready.");
});
