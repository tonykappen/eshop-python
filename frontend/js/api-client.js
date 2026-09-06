/**
 * Lightweight API client with auth header injection and 401 handling.
 */

function createApiClient(options) {
    const apiBase = options.apiBase;
    const getToken = options.getToken || function () {
        return localStorage.getItem('access_token');
    };
    const onUnauthorized = options.onUnauthorized || function (response) {
        if (typeof handleUnauthorizedResponse === 'function') {
            handleUnauthorizedResponse(response);
        }
    };

    async function request(path, init) {
        const token = getToken();
        const headers = Object.assign({}, (init && init.headers) || {});
        if (token && !headers.Authorization) {
            headers.Authorization = `Bearer ${token}`;
        }

        const response = await fetch(`${apiBase}${path}`, Object.assign({}, init, { headers }));

        if (response.status === 401) {
            onUnauthorized(response);
            return response;
        }

        return response;
    }

    return {
        request,
        get: function (path, init) {
            return request(path, Object.assign({}, init, { method: 'GET' }));
        },
        post: function (path, body, init) {
            return request(
                path,
                Object.assign({}, init, {
                    method: 'POST',
                    headers: Object.assign(
                        { 'Content-Type': 'application/json' },
                        (init && init.headers) || {}
                    ),
                    body: JSON.stringify(body),
                })
            );
        },
        delete: function (path, init) {
            return request(path, Object.assign({}, init, { method: 'DELETE' }));
        },
    };
}

function getApiBaseFromConfig() {
    if (typeof window !== 'undefined' && window.APP_CONFIG && window.APP_CONFIG.API_BASE) {
        return window.APP_CONFIG.API_BASE;
    }
    return 'http://localhost:8000';
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createApiClient,
        getApiBaseFromConfig,
    };
}
