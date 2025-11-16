#!/bin/bash
# Generate config.js from environment variables
# This script creates a config.js file with values from environment variables
# Usage: ./generate-config.sh > config.js

cat <<EOF
/**
 * Frontend Configuration
 * 
 * This file is auto-generated from environment variables.
 * DO NOT EDIT MANUALLY - it will be overwritten.
 * 
 * To regenerate: ./generate-config.sh > config.js
 */

window.APP_CONFIG = window.APP_CONFIG || {
    // API Configuration
    API_BASE: '${API_BASE:-http://localhost:8000}',
    
    // Keycloak Client Configuration
    KEYCLOAK_CLIENT_ID: '${KEYCLOAK_CLIENT_ID:-eshop-api}',
    KEYCLOAK_CLIENT_SECRET: '${KEYCLOAK_CLIENT_SECRET:-}',
    
    // Keycloak Server Configuration
    KEYCLOAK_SERVER_URL: '${KEYCLOAK_SERVER_URL:-http://localhost:8080}',
    KEYCLOAK_REALM: '${KEYCLOAK_REALM:-eshop}'
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
EOF

