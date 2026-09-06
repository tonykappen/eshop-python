const fs = require('fs');
const path = require('path');
const { E2E_API_URL, E2E_USER_PASSWORD, USERS } = require('./constants');

const TOKENS_PATH = path.join(__dirname, '..', '.auth', 'tokens.json');

async function fetchToken(username, password = E2E_USER_PASSWORD) {
  const body = new URLSearchParams({
    username,
    password,
    grant_type: 'password',
  });

  const response = await fetch(`${E2E_API_URL}/api/v1/auth-proxy/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Auth failed for ${username}: ${response.status} ${text}`);
  }

  const data = await response.json();
  return data.access_token;
}

function readCachedTokens() {
  if (!fs.existsSync(TOKENS_PATH)) {
    return null;
  }

  return JSON.parse(fs.readFileSync(TOKENS_PATH, 'utf8'));
}

function getCachedToken(username) {
  const tokens = readCachedTokens();
  if (!tokens) {
    return null;
  }

  const role = Object.entries(USERS).find(([, name]) => name === username)?.[0];
  return role ? tokens[role] : null;
}

async function ensureAuthTokensCached() {
  const dir = path.dirname(TOKENS_PATH);
  fs.mkdirSync(dir, { recursive: true });

  const tokens = {};
  for (const [role, username] of Object.entries(USERS)) {
    tokens[role] = await fetchToken(username);
  }

  fs.writeFileSync(TOKENS_PATH, JSON.stringify(tokens, null, 2));
  return tokens;
}

module.exports = {
  TOKENS_PATH,
  fetchToken,
  readCachedTokens,
  getCachedToken,
  ensureAuthTokensCached,
};
