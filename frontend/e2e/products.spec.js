const { test, expect } = require('@playwright/test');
const { loginViaAPI } = require('./helpers/auth');
const { USERS } = require('./helpers/constants');

test.describe('Products page', () => {
  test('displays product grid for authenticated user', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });

    await expect(page.locator('#productsGrid')).toBeVisible();
    await expect(page.locator('.product-card').first()).toBeVisible();
  });

  test('search filters products', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });

    const firstProductName = await page.locator('.product-card h3').first().textContent();
    expect(firstProductName).toBeTruthy();

    await page.locator('#searchTerm').fill(firstProductName.trim());
    await page.getByRole('button', { name: 'Search' }).click();
    await page.waitForResponse((response) =>
      response.url().includes('/api/v1/products/') && response.request().method() === 'GET'
    );

    await expect(page.locator('.product-card').first()).toBeVisible();
    await expect(page.locator('.product-card h3').first()).toContainText(firstProductName.trim());
  });

  test('pagination navigates to next page when available', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });

    const nextButton = page.locator('#pagination button', { hasText: 'Next' });
    if (await nextButton.isDisabled()) {
      test.skip();
    }

    const pageLabelBefore = await page.locator('#pagination span').textContent();
    await nextButton.click();
    await page.waitForResponse((response) =>
      response.url().includes('/api/v1/products/') && response.request().method() === 'GET'
    );

    const pageLabelAfter = await page.locator('#pagination span').textContent();
    expect(pageLabelAfter).not.toBe(pageLabelBefore);
  });

  test('admin can create a product', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.admin });

    await expect(page.locator('#createProductBtn')).toBeVisible();

    const uniqueName = `E2E Product ${Date.now()}`;
    await page.locator('#createProductBtn').click();
    await expect(page.locator('#productModal')).toBeVisible();

    await page.locator('#productName').fill(uniqueName);
    await page.locator('#productDescription').fill('Created by Playwright E2E test');
    await page.locator('#productPrice').fill('19.99');
    await page.locator('#categoryInput').fill('E2E');
    await page.getByRole('button', { name: 'Add', exact: true }).click();

    await page.locator('#submitBtn').click();
    await page.waitForResponse((response) =>
      response.url().includes('/api/v1/products') && response.request().method() === 'POST'
    );

    await expect(page.locator('#productModal')).toBeHidden();
    await expect(page.locator('.product-card h3', { hasText: uniqueName })).toBeVisible();
  });
});
