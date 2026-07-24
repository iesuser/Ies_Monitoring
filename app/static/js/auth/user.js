// Open the modal for editing a User record
function safeShowAlert(type, message) {
    if (typeof showAlert === "function") {
        showAlert("alertPlaceholder", type, message);
        return;
    }
    // Fallback so UX still works if shared alert helper is missing.
    window.alert(message);
}

function safeClearSession() {
    if (typeof clearSessionData === "function") {
        clearSessionData();
        return;
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    const i18n = window.I18n;
    window.location.href = i18n ? i18n.localizePath("/login") : "/login";
}

async function apiRequest(path, options = {}) {
    const token = localStorage.getItem("access_token");
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(path, {
        credentials: "include",
        ...options,
        headers,
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : null;

    if (!response.ok) {
        const errorMessage = data?.message || data?.error || "Request failed.";
        throw new Error(errorMessage);
    }

    return data;
}

async function openUserModal() {
    const i18n = window.I18n;
    const token = localStorage.getItem("access_token");
    if (!token) {
        safeShowAlert(
            "danger",
            i18n ? i18n.t("alerts.session_expired", "Session has expired. Please sign in again.") : "Session has expired. Please sign in again."
        );
        safeClearSession();
        return;
    }

    const emailText = document.getElementById("user_email");
    const roleText = document.getElementById("user_role");
    const accountsButton = document.getElementById("accountsButton");

    try {
        const data = await apiRequest("/api/accounts/user", { method: "GET" });

        if (!data || data.error) {
            safeShowAlert("danger", data?.error || "An error occurred while fetching data.");
            return;
        }

        document.getElementById("userUUID").value = data.uuid;
        document.getElementById("user_name").value = data.first_name || "";
        document.getElementById("user_lastname").value = data.last_name || "";
        emailText.textContent = data.email;
        roleText.textContent = data.is_active ? "Active" : "Inactive";

        if (accountsButton) {
            // Role-based exposure is not available in current /api/user payload.
            accountsButton.style.display = "none";
        }

        const modal = new bootstrap.Modal(document.getElementById("UserModal"));
        modal.show();
    } catch (error) {
        console.error("Error fetching data:", error);
        safeShowAlert("danger", error.message || "An error occurred while fetching data.");
    }
}

// Redirect to the accounts page
function redirectToAccounts() {
    const i18n = window.I18n;
    window.location.href = i18n ? i18n.localizePath('/accounts') : '/accounts';
}

function submitUserForm(event) {
    event.preventDefault();

    const i18n = window.I18n;
    const payload = {
        first_name: (document.getElementById("user_name").value || "").trim(),
        last_name: (document.getElementById("user_lastname").value || "").trim(),
    };

    apiRequest("/api/accounts/user", {
        method: "PUT",
        body: JSON.stringify(payload),
    })
        .then(() => {
            closeModal("UserModal");
            window.location.reload();
        })
        .catch((error) => {
            console.error("Error:", error);
            safeShowAlert(
                "danger",
                error.message || (i18n ? i18n.t("alerts.request_failed", "Request failed. Please try again.") : "Request failed. Please try again.")
            );
        });
}

function changePassword() {
    const i18n = window.I18n;
    window.location.href = i18n ? i18n.localizePath("/change_password") : "/change_password";
}

function closeModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    const instance = bootstrap.Modal.getInstance(modalElement);
    if (instance) {
        instance.hide();
    } else {
        const created = new bootstrap.Modal(modalElement);
        created.hide();
    }
}

if (typeof window.openUserModal !== "function") {
    window.openUserModal = openUserModal;
}
if (typeof window.submitUserForm !== "function") {
    window.submitUserForm = submitUserForm;
}
if (typeof window.redirectToAccounts !== "function") {
    window.redirectToAccounts = redirectToAccounts;
}
if (typeof window.changePassword !== "function") {
    window.changePassword = changePassword;
}