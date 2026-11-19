/*
  SafeVillage frontend connection.

  API_BASE is empty when this page is served by the FastAPI app
  (http://127.0.0.1:8000). Set window.SAFEVILLAGE_API_BASE before this
  script if the API lives on another origin.
*/

const API_BASE = window.SAFEVILLAGE_API_BASE || "";
const TOKEN_KEY = "safevillage_token";

const state = {
    user: null,
    authMode: "login",
};

document.addEventListener("DOMContentLoaded", () => {
    bindNavigation();
    bindAuth();
    bindComplaints();
    bindSchemes();
    bindLocations();
    bindAssistant();
    bindAdmin();
    loadEmergencyContacts();
    restoreSession();
});

function bindNavigation() {
    const menu = document.getElementById("menu-btn");
    const navbar = document.querySelector(".navbar");
    menu.addEventListener("click", () => {
        const open = navbar.classList.toggle("open");
        menu.setAttribute("aria-expanded", open ? "true" : "false");
    });
    navbar.querySelectorAll("nav a, .nav-actions button").forEach((item) => {
        item.addEventListener("click", () => navbar.classList.remove("open"));
    });
}

async function api(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    if (options.body) {
        headers["Content-Type"] = "application/json";
    }
    let response;
    try {
        response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } catch (_error) {
        throw new Error("Could not reach the SafeVillage server. Start the backend and try again.");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const error = new Error(readableError(data, response.status));
        error.status = response.status;
        throw error;
    }
    return data;
}

function readableError(data, status) {
    if (Array.isArray(data.errors) && data.errors.length) {
        return data.errors.map((item) => item.message).join(" ");
    }
    if (typeof data.detail === "string") {
        return data.detail;
    }
    if (status === 401) {
        return "Please log in to continue.";
    }
    return "The server could not complete that request.";
}

function setMessage(id, text, kind) {
    const node = document.getElementById(id);
    node.textContent = text || "";
    node.className = `form-message${kind ? ` ${kind}` : ""}`;
}

function setBusy(button, busy, busyText) {
    if (!button.dataset.label) {
        button.dataset.label = button.textContent;
    }
    button.disabled = busy;
    button.textContent = busy ? busyText : button.dataset.label;
}

function bindAuth() {
    document.getElementById("login-open").addEventListener("click", () => openAuth("login"));
    document.getElementById("register-open").addEventListener("click", () => openAuth("register"));
    document.getElementById("auth-close").addEventListener("click", closeAuth);
    document.getElementById("logout-btn").addEventListener("click", logout);
    document.getElementById("auth-form").addEventListener("submit", submitAuth);
    document.getElementById("auth-modal").addEventListener("click", (event) => {
        if (event.target.id === "auth-modal") {
            closeAuth();
        }
    });
}

function openAuth(mode) {
    state.authMode = mode;
    const register = mode === "register";
    document.getElementById("auth-title").textContent = register ? "Register" : "Login";
    document.getElementById("auth-submit").textContent = register ? "Create account" : "Login";
    document.getElementById("auth-name").hidden = !register;
    document.getElementById("auth-village").hidden = !register;
    document.getElementById("auth-name").required = register;
    setMessage("auth-message", "");
    document.getElementById("auth-modal").hidden = false;
}

function closeAuth() {
    document.getElementById("auth-modal").hidden = true;
}

async function submitAuth(event) {
    event.preventDefault();
    const button = document.getElementById("auth-submit");
    setBusy(button, true, "Please wait...");
    setMessage("auth-message", "");
    try {
        if (state.authMode === "register") {
            await api("/api/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    full_name: document.getElementById("auth-name").value,
                    email: document.getElementById("auth-email").value,
                    password: document.getElementById("auth-password").value,
                    village: document.getElementById("auth-village").value || null,
                }),
            });
            openAuth("login");
            setMessage("auth-message", "Account created. Please log in.", "success");
        } else {
            const data = await api("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: document.getElementById("auth-email").value,
                    password: document.getElementById("auth-password").value,
                }),
            });
            if (!data.access_token) {
                throw new Error("Login did not return a session token.");
            }
            sessionStorage.setItem(TOKEN_KEY, data.access_token);
            state.user = data.user;
            renderSession();
            closeAuth();
        }
    } catch (error) {
        setMessage("auth-message", error.message, "error");
    } finally {
        setBusy(button, false);
    }
}

async function restoreSession() {
    if (!sessionStorage.getItem(TOKEN_KEY)) {
        renderSession();
        return;
    }
    try {
        state.user = await api("/api/auth/me");
    } catch (_error) {
        sessionStorage.removeItem(TOKEN_KEY);
        state.user = null;
    }
    renderSession();
}

function renderSession() {
    const loggedIn = Boolean(state.user);
    document.getElementById("login-open").hidden = loggedIn;
    document.getElementById("register-open").hidden = loggedIn;
    document.getElementById("logout-btn").hidden = !loggedIn;
    document.getElementById("admin-open").hidden = !loggedIn || state.user.role !== "administrator";
    const chip = document.getElementById("user-chip");
    chip.hidden = !loggedIn;
    chip.textContent = loggedIn ? state.user.full_name : "";
    if (loggedIn && !document.getElementById("complaint-name").value) {
        document.getElementById("complaint-name").value = state.user.full_name;
    }
}

async function logout() {
    try {
        await api("/api/auth/logout", { method: "POST" });
    } catch (_error) {
        // The local session is cleared even if the server is unreachable.
    }
    sessionStorage.removeItem(TOKEN_KEY);
    state.user = null;
    renderSession();
}

function bindComplaints() {
    document.getElementById("complaint-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = event.target.querySelector("button");
        if (!sessionStorage.getItem(TOKEN_KEY)) {
            setMessage("complaint-message", "Please register or log in before submitting a complaint.", "error");
            openAuth("login");
            return;
        }
        setBusy(button, true, "Submitting...");
        setMessage("complaint-message", "");
        try {
            const data = await api("/api/complaints", {
                method: "POST",
                body: JSON.stringify({
                    contact_name: document.getElementById("complaint-name").value,
                    contact_phone: document.getElementById("complaint-phone").value,
                    village: document.getElementById("complaint-village").value || null,
                    category: document.getElementById("complaint-category").value,
                    description: document.getElementById("complaint-description").value,
                }),
            });
            if (!data.tracking_id) {
                throw new Error("The server did not confirm a tracking ID.");
            }
            setMessage(
                "complaint-message",
                `${data.message} Status: ${data.status_label}.`,
                "success",
            );
            document.getElementById("tracking-id").value = data.tracking_id;
            event.target.reset();
            renderSession();
        } catch (error) {
            setMessage("complaint-message", error.message, "error");
        } finally {
            setBusy(button, false);
        }
    });

    document.getElementById("track-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const trackingId = document.getElementById("tracking-id").value.trim();
        if (!trackingId) {
            setMessage("track-message", "Enter the tracking ID you received.", "error");
            return;
        }
        if (!sessionStorage.getItem(TOKEN_KEY)) {
            setMessage("track-message", "Log in with the same account that created the complaint.", "error");
            openAuth("login");
            return;
        }
        setMessage("track-message", "Checking...");
        try {
            const data = await api(`/api/complaints/${encodeURIComponent(trackingId)}`);
            const history = (data.history || [])
                .map((item) => `${item.new_status_label}${item.note ? `: ${item.note}` : ""}`)
                .join(" | ");
            setMessage(
                "track-message",
                `${data.tracking_id} is ${data.status_label}. ${data.disclaimer} ${history}`,
                "success",
            );
        } catch (error) {
            setMessage("track-message", error.message, "error");
        }
    });
}

async function bindSchemes() {
    document.getElementById("scheme-search-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const query = document.getElementById("scheme-query").value.trim();
        if (query.length < 2) {
            setMessage("scheme-message", "Enter at least 2 characters to search.", "error");
            return;
        }
        await loadSchemes(`/api/schemes/search?q=${encodeURIComponent(query)}`);
    });
    await loadSchemes("/api/schemes");
}

async function loadSchemes(path) {
    try {
        const data = await api(path);
        const grid = document.getElementById("schemes-grid");
        grid.replaceChildren();
        data.schemes.forEach((scheme) => {
            const card = document.createElement("article");
            card.className = "scheme-card";
            const icon = document.createElement("i");
            icon.className = "fa-solid fa-file-circle-check";
            const title = document.createElement("h3");
            title.textContent = scheme.short_name;
            const text = document.createElement("p");
            text.textContent = `${scheme.name}. ${scheme.is_demo ? "Demo record." : ""} ${scheme.verification_note}`;
            card.append(icon, title, text);
            if (typeof scheme.official_url === "string" && scheme.official_url.startsWith("https://")) {
                const link = document.createElement("a");
                link.href = scheme.official_url;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                link.textContent = "Official Website ↗";
                card.append(link);
            }
            const details = document.createElement("p");
            details.textContent = scheme.eligibility;
            card.append(details);
            grid.append(card);
        });
        setMessage("scheme-message", data.notice, "success");
        if (!data.schemes.length) {
            setMessage("scheme-message", "No demo schemes matched that search.", "error");
        }
    } catch (error) {
        setMessage("scheme-message", `${error.message} The original scheme links are still shown.`, "error");
    }
}

function bindLocations() {
    const form = document.getElementById("map-search-form");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        await searchLocations(document.getElementById("map-query").value.trim(), null);
    });
    document.querySelectorAll("[data-location-category]").forEach((card) => {
        card.addEventListener("click", () => {
            const category = card.getAttribute("data-location-category");
            document.getElementById("map-query").value = category.replaceAll("_", " ");
            searchLocations(category.replaceAll("_", " "), category);
        });
    });
    loadLocationCategories();
}

async function loadLocationCategories() {
    try {
        const data = await api("/api/locations/categories");
        const row = document.getElementById("location-categories");
        data.categories.forEach((category) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "chip";
            button.textContent = category.label;
            button.addEventListener("click", () => {
                document.getElementById("map-query").value = category.label;
                searchLocations(category.label, category.code);
            });
            row.append(button);
        });
    } catch (error) {
        setMessage("map-message", error.message, "error");
    }
}

async function searchLocations(query, category) {
    if (query.length < 2) {
        setMessage("map-message", "Enter at least 2 characters.", "error");
        return;
    }
    setMessage("map-message", "Searching...");
    const params = new URLSearchParams({ q: query });
    if (category) {
        params.set("category", category);
    }
    try {
        const data = await api(`/api/locations/search?${params.toString()}`);
        renderLocationResults(data);
    } catch (error) {
        const fallback = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
        setMessage("map-message", `${error.message} Public Google Maps search is still available.`, "error");
        const list = document.getElementById("map-results");
        list.replaceChildren();
        const link = document.createElement("a");
        link.className = "result-link";
        link.href = fallback;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Open this search in Google Maps";
        list.append(link);
    }
}

function renderLocationResults(data) {
    setMessage("map-message", data.disclaimer, "success");
    const list = document.getElementById("map-results");
    list.replaceChildren();
    data.results.forEach((place) => {
        const link = document.createElement("a");
        link.className = "result-link";
        link.href = place.maps_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        const distance = place.distance_km == null ? "" : ` · ${place.distance_km} km`;
        link.textContent = `${place.sample ? "Sample: " : ""}${place.name} · ${place.area}${distance}`;
        list.append(link);
    });
    const first = data.results[0];
    if (first && first.maps_url) {
        const embedQuery = new URL(first.maps_url).searchParams.get("query") || data.query;
        document.getElementById("map-frame").src = `https://www.google.com/maps?q=${encodeURIComponent(embedQuery)}&output=embed`;
    }
}

async function loadEmergencyContacts() {
    try {
        const data = await api("/api/emergency/contacts");
        const grid = document.getElementById("emergency-grid");
        grid.replaceChildren();
        data.contacts.forEach((contact) => {
            const card = document.createElement("a");
            card.className = "emergency-card";
            card.href = `tel:${contact.phone}`;
            const icon = document.createElement("i");
            icon.className = "fa-solid fa-phone";
            const number = document.createElement("h3");
            number.textContent = contact.phone;
            const name = document.createElement("p");
            name.textContent = contact.name;
            card.append(icon, number, name);
            grid.append(card);
        });
        document.getElementById("emergency-note").textContent = data.disclaimer;
    } catch (_error) {
        document.getElementById("emergency-note").textContent =
            "The contact list could not be refreshed. The numbers already shown are informational. Call 112 yourself in an emergency. SafeVillage does not dispatch help.";
    }
}

function bindAssistant() {
    document.getElementById("open-assistant").addEventListener("click", (event) => {
        event.preventDefault();
        openAssistant();
    });
    document.querySelectorAll("[data-chat-prompt]").forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            document.getElementById("chat-language").value = link.getAttribute("data-chat-language") || "en";
            document.getElementById("chat-message").value = link.getAttribute("data-chat-prompt");
            openAssistant();
        });
    });
    document.getElementById("assistant-close").addEventListener("click", () => {
        document.getElementById("assistant").hidden = true;
    });
    document.getElementById("chat-form").addEventListener("submit", sendChat);
    api("/api/ai/health").then((health) => {
        const mode = health.provider_configured
            ? "An AI provider is configured. Replies are still general information, not a government decision."
            : "Demo fallback is active because no AI API key is configured. Replies are clearly labelled.";
        document.getElementById("assistant-mode").textContent = mode;
    }).catch(() => {
        document.getElementById("assistant-mode").textContent = "The assistant server is not reachable.";
    });
}

function openAssistant() {
    document.getElementById("assistant").hidden = false;
    document.getElementById("chat-message").focus();
}

async function sendChat(event) {
    event.preventDefault();
    const input = document.getElementById("chat-message");
    const message = input.value.trim();
    const button = event.target.querySelector("button");
    if (message.length < 2) {
        setMessage("chat-message-status", "Please enter a question.", "error");
        return;
    }
    appendChat("user", message);
    input.value = "";
    setBusy(button, true, "Sending...");
    setMessage("chat-message-status", "");
    try {
        const data = await api("/api/ai/chat", {
            method: "POST",
            body: JSON.stringify({
                message,
                language: document.getElementById("chat-language").value,
            }),
        });
        const prefix = data.demo_label ? `${data.demo_label}\n` : "";
        appendChat("assistant", `${prefix}${data.reply}\n${data.disclaimer}`);
    } catch (error) {
        setMessage("chat-message-status", error.message, "error");
    } finally {
        setBusy(button, false);
    }
}

function appendChat(role, text) {
    const log = document.getElementById("chat-log");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    bubble.textContent = text;
    log.append(bubble);
    log.scrollTop = log.scrollHeight;
}

function bindAdmin() {
    document.getElementById("admin-open").addEventListener("click", openAdmin);
    document.getElementById("admin-close").addEventListener("click", () => {
        document.getElementById("admin-panel").hidden = true;
    });
}

async function openAdmin() {
    document.getElementById("admin-panel").hidden = false;
    setMessage("admin-message", "Loading dashboard...");
    try {
        const [dashboard, complaints] = await Promise.all([
            api("/api/admin/dashboard"),
            api("/api/admin/complaints"),
        ]);
        renderAdmin(dashboard, complaints);
        setMessage("admin-message", "Dashboard loaded. Updating a status does not notify a government office.", "success");
    } catch (error) {
        setMessage("admin-message", error.message, "error");
    }
}

function renderAdmin(dashboard, complaints) {
    const stats = document.getElementById("admin-stats");
    stats.replaceChildren();
    [
        ["Citizens", dashboard.total_citizens],
        ["Complaints", dashboard.total_complaints],
        ["Pending", dashboard.pending_complaints],
        ["Resolved", dashboard.resolved_complaints],
    ].forEach(([label, value]) => {
        const box = document.createElement("div");
        const number = document.createElement("strong");
        number.textContent = String(value);
        box.append(number, document.createTextNode(label));
        stats.append(box);
    });

    const list = document.getElementById("admin-complaints");
    list.replaceChildren();
    complaints.forEach((complaint) => {
        const card = document.createElement("article");
        card.className = "admin-card";
        const title = document.createElement("h3");
        title.textContent = `${complaint.tracking_id} · ${complaint.status_label}`;
        const text = document.createElement("p");
        text.textContent = `${complaint.category_label}${complaint.village ? ` · ${complaint.village}` : ""} · ${complaint.description}`;
        const select = document.createElement("select");
        ["pending", "under_review", "in_progress", "resolved", "rejected"].forEach((status) => {
            const option = document.createElement("option");
            option.value = status;
            option.textContent = status.replaceAll("_", " ");
            option.selected = status === complaint.status;
            select.append(option);
        });
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "Update status";
        button.addEventListener("click", async () => {
            button.disabled = true;
            try {
                await api(`/api/admin/complaints/${encodeURIComponent(complaint.tracking_id)}`, {
                    method: "PATCH",
                    body: JSON.stringify({
                        status: select.value,
                        note: "Updated from the SafeVillage admin demo.",
                    }),
                });
                setMessage("admin-message", `${complaint.tracking_id} is now ${select.value.replaceAll("_", " ")}.`, "success");
                openAdmin();
            } catch (error) {
                setMessage("admin-message", error.message, "error");
                button.disabled = false;
            }
        });
        card.append(title, text, select, button);
        list.append(card);
    });
}
