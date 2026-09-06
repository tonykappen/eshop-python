const { test, expect } = require('@playwright/test');
const { loginViaAPI } = require('./helpers/auth');
const { USERS } = require('./helpers/constants');

test.describe('Manager product CRUD', () => {
  test('manager can create, edit, and delete a product', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.manager });

    const uniqueName = `E2E Manager Product ${Date.now()}`;

    await page.locator('#createProductBtn').click();
    await page.locator('#productName').fill(uniqueName);
    await page.locator('#productDescription').fill('Manager CRUD test product');
    await page.locator('#productPrice').fill('42.50');
    await page.locator('#categoryInput').fill('e2e-manager');
    await page.getByRole('button', { name: 'Add', exact: true }).click();
    await page.locator('#submitBtn').click();

    page.once('dialog', (dialog) => dialog.accept());
    await expect(page.getByText(uniqueName)).toBeVisible({ timeout: 15000 });

    const card = page.locator('.product-card', { hasText: uniqueName });
    await card.getByRole('button', { name: 'Edit' }).click();
    const updatedName = `${uniqueName} Updated`;
    await page.locator('#productName').fill(updatedName);
    await page.locator('#submitBtn').click();

    page.once('dialog', (dialog) => dialog.accept());
    await expect(page.getByText(updatedName)).toBeVisible({ timeout: 15000 });

    const updatedCard = page.locator('.product-card', { hasText: updatedName });
    page.once('dialog', (dialog) => dialog.accept());
    await updatedCard.getByRole('button', { name: 'Delete' }).click();

    page.once('dialog', (dialog) => dialog.accept());
    await expect(page.getByText(updatedName)).toHaveCount(0, { timeout: 15000 });
  });
});
