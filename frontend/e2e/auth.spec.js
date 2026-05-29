const { test, expect } = require('@playwright/test');
const { loginViaUI, loginViaAPI, getToken, injectAuth } = require('./helpers/auth');
const { USERS, E2E_USER_PASSWORD } = require('./helpers/constants');

test.describe('Authentication', () => {
  test('logs in with valid credentials and lands on products page', async ({ page }) => {
    await loginViaUI(page, { username: USERS.user });

    await expect(page).toHaveURL(/products\.html/);
    await expect(page.locator('#username')).toHaveText(USERS.user);
    await expect(page.locator('#productsGrid')).toBeVisible();
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/index.html');
    await page.fill('#username', USERS.user);
    await page.fill('#password', 'wrong-password');

    const authResponse = page.waitForResponse(
      (response) => response.url().includes('/api/v1/auth-proxy/token'),
      { timeout: 30_000 }
    );
    await page.click('button[type="submit"]');
    const response = await authResponse;

    expect(response.ok()).toBe(false);
    await expect(page).toHaveURL(/index\.html/);
    await expect(page.locator('#error')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#error')).toContainText(/invalid/i);
  });

  test('redirects to products when a valid token is already stored', async ({ page, request }) => {
    const token = await getToken(request, { username: USERS.user });
    await injectAuth(page, { token, username: USERS.user });

    await page.goto('/index.html');
    await page.waitForURL('**/products.html');
    await expect(page.locator('#productsGrid')).toBeVisible();
  });

  test('logout clears session and returns to login', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });
    await page.getByRole('button', { name: 'Logout' }).click();

    await expect(page).toHaveURL(/index\.html/);
    const storage = await page.evaluate(() => ({
      token: localStorage.getItem('access_token'),
      username: localStorage.getItem('username'),
    }));
    expect(storage.token).toBeNull();
    expect(storage.username).toBeNull();
  });
});
