/**
 * Frontend Configuration
 * 
 * This file contains configuration values for the frontend application.
 * In production, these values should be set from environment variables.
 * 
 * To generate this file from environment variables:
 * 1. Bash: ./generate-config.sh > config.js
 * 2. Node.js: node generate-config.js
 * 3. Or manually edit the values below
 * 
 * IMPORTANT: Do not commit secrets to version control!
 * Use environment variables or a .env file (not committed).
 */

// Default configuration values
// These can be overridden by environment variables or build process
// For production, generate this file using generate-config.sh or generate-config.js
window.APP_CONFIG = window.APP_CONFIG || {
    // API Configuration
    API_BASE: 'http://localhost:8000',
    
    // Keycloak Client Configuration
    // NOTE: client_id and client_secret are NO LONGER NEEDED in frontend
    // The backend handles client credentials server-side for security
    // These are kept for backward compatibility but not used
    KEYCLOAK_CLIENT_ID: 'eshop-api',
    KEYCLOAK_CLIENT_SECRET: '', // Not used - backend handles this server-side
    
    // Keycloak Server Configuration
    KEYCLOAK_SERVER_URL: 'http://localhost:8080',
    KEYCLOAK_REALM: 'eshop'
};

// Fallback: Try to read from meta tags if available (for server-side injection)
(function() {
    const metaClientId = document.querySelector('meta[name="keycloak-client-id"]');
    const metaClientSecret = document.querySelector('meta[name="keycloak-client-secret"]');
    const metaApiBase = document.querySelector('meta[name="api-base"]');
    
    if (metaClientId) {
        window.APP_CONFIG.KEYCLOAK_CLIENT_ID = metaClientId.getAttribute('content');
    }
    if (metaClientSecret) {
        window.APP_CONFIG.KEYCLOAK_CLIENT_SECRET = metaClientSecret.getAttribute('content');
    }
    if (metaApiBase) {
        window.APP_CONFIG.API_BASE = metaApiBase.getAttribute('content');
    }
})();

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.APP_CONFIG;
}

