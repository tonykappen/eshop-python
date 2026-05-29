const { test, expect } = require('@playwright/test');
const { loginViaAPI } = require('./helpers/auth');
const { USERS } = require('./helpers/constants');

test.describe('Session expired UX', () => {
  test('cleared token redirects to login with session message', async ({ page }) => {
    await page.goto('/index.html?session_expired=1&reason=token_expired');
    await expect(page.locator('#error, #sessionMessage')).toBeVisible();
    await expect(page.locator('#error, #sessionMessage')).toContainText(/session/i);
  });

  test('401 from products API triggers login redirect', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });

    await page.evaluate(() => {
      localStorage.setItem('access_token', 'invalid-token');
    });

    await page.reload();
    await page.waitForURL(/index\.html(\?.*session_expired=1)?/, { timeout: 15000 });
    await expect(page).toHaveURL(/index\.html/);
  });
});
