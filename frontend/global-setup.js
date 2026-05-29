const { E2E_API_URL, E2E_BASE_URL, E2E_USER_PASSWORD, USERS } = require('./e2e/helpers/constants');
const { ensureAuthTokensCached } = require('./e2e/helpers/tokens');

async function waitForOk(url, options = {}) {
  const { timeoutMs = 120_000, intervalMs = 3_000, label = url } = options;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // retry
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error(`Timed out waiting for ${label}`);
}

async function waitForAuthReady() {
  const deadline = Date.now() + 120_000;

  while (Date.now() < deadline) {
    try {
      const body = new URLSearchParams({
        username: USERS.user,
        password: E2E_USER_PASSWORD,
        grant_type: 'password',
      });

      const response = await fetch(`${E2E_API_URL}/api/v1/auth-proxy/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });

      if (response.ok) {
        return;
      }
    } catch {
      // retry
    }
    await new Promise((resolve) => setTimeout(resolve, 3_000));
  }

  throw new Error('Timed out waiting for auth-proxy/token');
}

async function waitForSeededProducts() {
  const tokenResponse = await fetch(`${E2E_API_URL}/api/v1/auth-proxy/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      username: USERS.user,
      password: E2E_USER_PASSWORD,
      grant_type: 'password',
    }),
  });

  if (!tokenResponse.ok) {
    throw new Error('Unable to authenticate while waiting for seeded products');
  }

  const { access_token: token } = await tokenResponse.json();
  const deadline = Date.now() + 120_000;

  while (Date.now() < deadline) {
    const response = await fetch(`${E2E_API_URL}/api/v1/products/?page=1&page_size=1`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data.items) && data.items.length > 0) {
        return;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 3_000));
  }

  throw new Error('Timed out waiting for seeded catalog products');
}

module.exports = async function globalSetup() {
  if (process.env.PLAYWRIGHT_SKIP_GLOBAL_SETUP === '1') {
    return;
  }

  await waitForOk(`${E2E_API_URL}/health`, { label: 'backend /health' });
  await waitForOk(`${E2E_BASE_URL}/`, { label: 'frontend /' });
  await waitForAuthReady();
  await waitForSeededProducts();
  await ensureAuthTokensCached();
};
