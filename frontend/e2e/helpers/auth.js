const fs = require('fs');
const path = require('path');
const { E2E_API_URL, E2E_USER_PASSWORD } = require('./constants');
const { fetchToken, getCachedToken } = require('./tokens');

async function getToken(request, { username, password = E2E_USER_PASSWORD }) {
  const cached = getCachedToken(username);
  if (cached) {
    return cached;
  }

  const response = await request.post(`${E2E_API_URL}/api/v1/auth-proxy/token`, {
    form: {
      username,
      password,
      grant_type: 'password',
    },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`Auth failed for ${username}: ${response.status()} ${body}`);
  }

  const data = await response.json();
  return data.access_token;
}

async function injectAuth(page, { token, username }) {
  await page.goto('/index.html');
  await page.evaluate(
    ({ tokenValue, usernameValue }) => {
      localStorage.setItem('access_token', tokenValue);
      localStorage.setItem('username', usernameValue);
    },
    { tokenValue: token, usernameValue: username }
  );
}

/**
 * Fast, reliable login for most e2e tests (avoids hammering the login form).
 */
async function loginViaAPI(page, request, { username, password = E2E_USER_PASSWORD }) {
  let token = getCachedToken(username);
  if (!token) {
    token = await getToken(request, { username, password });
  }
  await injectAuth(page, { token, username });
  await page.goto('/products.html');
  await page.locator('#productsGrid').waitFor({ state: 'visible', timeout: 30_000 });
}

async function loginViaUI(page, { username, password = E2E_USER_PASSWORD }) {
  await page.goto('/index.html');
  await page.fill('#username', username);
  await page.fill('#password', password);

  const navigation = page.waitForURL('**/products.html', { timeout: 60_000 });
  await page.click('button[type="submit"]');
  await navigation;
  await page.locator('#productsGrid').waitFor({ state: 'visible', timeout: 30_000 });
}

async function saveStorageState(page, filePath) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });

  const storage = await page.context().storageState();
  fs.writeFileSync(filePath, JSON.stringify(storage, null, 2));
}

module.exports = {
  getToken,
  loginViaAPI,
  loginViaUI,
  injectAuth,
  saveStorageState,
};
