#!/usr/bin/env node
/**
 * Generate config.js from environment variables (Node.js version)
 * Usage: node generate-config.js > config.js
 * Or: KEYCLOAK_CLIENT_SECRET=secret node generate-config.js > config.js
 */

const fs = require('fs');
const path = require('path');

// Read environment variables with defaults
const config = {
    API_BASE: process.env.API_BASE || 'http://localhost:8000',
    KEYCLOAK_CLIENT_ID: process.env.KEYCLOAK_CLIENT_ID || 'eshop-api',
    KEYCLOAK_CLIENT_SECRET: process.env.KEYCLOAK_CLIENT_SECRET || '',
    KEYCLOAK_SERVER_URL: process.env.KEYCLOAK_SERVER_URL || 'http://localhost:8080',
    KEYCLOAK_REALM: process.env.KEYCLOAK_REALM || 'eshop'
};

// Generate config.js content
const configContent = `/**
 * Frontend Configuration
 * 
 * This file is auto-generated from environment variables.
 * DO NOT EDIT MANUALLY - it will be overwritten.
 * 
 * To regenerate: node generate-config.js > config.js
 * Or: ./generate-config.sh > config.js
 */

window.APP_CONFIG = window.APP_CONFIG || {
    // API Configuration
    API_BASE: '${config.API_BASE}',
    
    // Keycloak Client Configuration
    KEYCLOAK_CLIENT_ID: '${config.KEYCLOAK_CLIENT_ID}',
    KEYCLOAK_CLIENT_SECRET: '${config.KEYCLOAK_CLIENT_SECRET}',
    
    // Keycloak Server Configuration
    KEYCLOAK_SERVER_URL: '${config.KEYCLOAK_SERVER_URL}',
    KEYCLOAK_REALM: '${config.KEYCLOAK_REALM}'
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
`;

// Write to config.js
const configPath = path.join(__dirname, 'config.js');
fs.writeFileSync(configPath, configContent, 'utf8');
console.log(`✅ Generated config.js at ${configPath}`);
console.log(`   API_BASE: ${config.API_BASE}`);
console.log(`   KEYCLOAK_CLIENT_ID: ${config.KEYCLOAK_CLIENT_ID}`);
console.log(`   KEYCLOAK_CLIENT_SECRET: ${config.KEYCLOAK_CLIENT_SECRET ? '***' : '(not set)'}`);
console.log(`   KEYCLOAK_SERVER_URL: ${config.KEYCLOAK_SERVER_URL}`);
console.log(`   KEYCLOAK_REALM: ${config.KEYCLOAK_REALM}`);

