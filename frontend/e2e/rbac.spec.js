const { test, expect } = require('@playwright/test');
const { loginViaAPI } = require('./helpers/auth');
const { USERS } = require('./helpers/constants');

test.describe('Role-based UI visibility', () => {
  test('regular user sees cart actions and not admin controls', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.user });

    await expect(page.locator('#createProductBtn')).toBeHidden();
    await expect(page.locator('#headerBasketBtn')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add to Cart' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Edit' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Delete' })).toHaveCount(0);
  });

  test('manager sees product management controls and not cart actions', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.manager });

    await expect(page.locator('#createProductBtn')).toBeVisible();
    await expect(page.locator('#headerBasketBtn')).toBeHidden();
    await expect(page.getByRole('button', { name: 'Add to Cart' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Edit' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Delete' }).first()).toBeVisible();
  });

  test('admin sees product management controls and not cart actions', async ({ page, request }) => {
    await loginViaAPI(page, request, { username: USERS.admin });

    await expect(page.locator('#createProductBtn')).toBeVisible();
    await expect(page.locator('#headerBasketBtn')).toBeHidden();
    await expect(page.getByRole('button', { name: 'Add to Cart' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Edit' }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Delete' }).first()).toBeVisible();
  });
});
