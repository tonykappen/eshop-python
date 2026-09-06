const { test, expect } = require('@playwright/test');
const { loginAndCheckoutOrder } = require('./helpers/checkout');
const { USERS } = require('./helpers/constants');

test.describe('Orders page', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginAndCheckoutOrder(page, request, USERS.user);
  });

  test('displays order history after checkout', async ({ page }) => {
    await expect(page.locator('#ordersContent')).toBeVisible();
    await expect(page.locator('#ordersList .order-card').first()).toBeVisible();
    await expect(page.locator('#emptyOrders')).toBeHidden();
  });

  test('opens order detail modal', async ({ page }) => {
    await page.locator('.view-btn').first().click();
    await expect(page.locator('#orderDetailModal')).toBeVisible();
    await expect(page.locator('#orderDetailContent')).not.toBeEmpty();
  });

  test('pagination controls appear when multiple pages exist', async ({ page }) => {
    const nextButton = page.locator('#pagination button', { hasText: 'Next' });
    if (await nextButton.isDisabled()) {
      await expect(page.locator('#pagination')).toBeVisible();
      return;
    }

    await nextButton.click();
    await page.waitForResponse((response) =>
      response.url().includes('/api/v1/orders') && response.request().method() === 'GET'
    );
    await expect(page.locator('#pagination span')).toContainText('Page');
  });
});
