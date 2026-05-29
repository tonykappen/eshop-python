const { test, expect } = require('@playwright/test');
const { loginViaAPI } = require('./helpers/auth');
const { addFirstProductToCart, fillCheckoutForm, waitForBasketReady } = require('./helpers/checkout');
const { USERS } = require('./helpers/constants');

test.describe('Basket page', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });
    await addFirstProductToCart(page);
    await waitForBasketReady(page);
  });

  test('shows basket items after adding from products page', async ({ page }) => {
    await expect(page.locator('#basketItems .basket-item').first()).toBeVisible();
    await expect(page.locator('#emptyBasket')).toBeHidden();
  });

  test('updates quantity and recalculates total', async ({ page }) => {
    const totalBefore = (await page.locator('#total').textContent())?.trim();

    page.on('dialog', (dialog) => dialog.accept());

    const basketReload = page.waitForResponse(
      (response) =>
        response.url().includes('/api/v1/basket/') &&
        response.request().method() === 'GET' &&
        response.ok()
    );

    await page.locator('.quantity-btn', { hasText: '+' }).first().click();
    await basketReload;

    await expect(page.locator('#total')).not.toHaveText(totalBefore, { timeout: 15_000 });
  });

  test('removes item from basket', async ({ page }) => {
    page.on('dialog', (dialog) => dialog.accept());
    await page.locator('.remove-btn').first().click();
    await page.waitForResponse((response) =>
      response.url().includes('/api/v1/basket/') && response.request().method() === 'DELETE'
    );

    await expect(page.locator('#emptyBasket')).toBeVisible();
  });

  test('completes checkout and redirects to orders', async ({ page }) => {
    await page.locator('#checkoutBtn').click();
    await page.locator('#checkoutForm').waitFor({ state: 'visible' });
    await fillCheckoutForm(page);

    page.once('dialog', (dialog) => dialog.accept());

    const checkoutResponse = page.waitForResponse(
      (response) =>
        response.url().includes('/checkout') &&
        response.request().method() === 'POST' &&
        response.ok()
    );
    await page.locator('#checkoutFormElement button[type="submit"]').click();
    await checkoutResponse;
    await page.waitForURL('**/orders.html', { timeout: 60_000 });

    await expect(page).toHaveURL(/orders\.html/);
  });
});
