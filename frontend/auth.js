/**
 * Shared auth helpers for eShop frontend pages.
 * Handles stale Keycloak tokens after docker volume wipes (kid rotation).
 */

function clearAuthStorage() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
}

function getAccessToken() {
    return localStorage.getItem('access_token');
}

function getAuthHeaders() {
    const token = getAccessToken();
    if (!token) {
        return {};
    }
    return { Authorization: `Bearer ${token}` };
}

/**
 * Call on 401 responses — clears storage and redirects to login with a message.
 */
function handleUnauthorized(detail) {
    clearAuthStorage();
    const params = new URLSearchParams();
    if (detail) {
        params.set('session_expired', '1');
        params.set('reason', String(detail).slice(0, 200));
    }
    const query = params.toString();
    window.location.href = query ? `index.html?${query}` : 'index.html';
}

/**
 * Validate stored token against backend before auto-redirecting from login page.
 */
async function validateStoredToken(apiBase) {
    const token = getAccessToken();
    if (!token) {
        return false;
    }
    try {
        const response = await fetch(`${apiBase}/api/v1/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (response.status === 401) {
            clearAuthStorage();
            return false;
        }
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Parse 401 response body and redirect to login with context.
 */
function handleUnauthorizedResponse(response) {
    response
        .json()
        .then((data) => {
            const detail = data.detail || data.message || 'session_expired';
            handleUnauthorized(detail);
        })
        .catch(() => handleUnauthorized('session_expired'));
}

function showSessionExpiredMessage() {
    const params = new URLSearchParams(window.location.search);
    if (!params.has('session_expired')) {
        return;
    }
    const reason = params.get('reason');
    const message =
        reason && reason.includes('stale_signing_key')
            ? 'Your session used an old sign-in key (Keycloak was reset). Please log in again.'
            : 'Your session has expired. Please log in again.';
    const el = document.getElementById('error') || document.getElementById('sessionMessage');
    if (el) {
        el.style.display = 'block';
        el.textContent = message;
        el.classList.add('error');
    }
}
