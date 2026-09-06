const { expect } = require('@playwright/test');
const { getToken } = require('../../e2e/helpers/auth');
const { USERS, E2E_USER_PASSWORD } = require('../../e2e/helpers/constants');

async function authenticate(request, username = USERS.user) {
  const token = await getToken(request, { username, password: E2E_USER_PASSWORD });
  return { Authorization: `Bearer ${token}` };
}

function assertPaginatedShape(data) {
  expect(data).toHaveProperty('items');
  expect(Array.isArray(data.items)).toBe(true);
  expect(typeof data.total).toBe('number');
  expect(typeof data.page).toBe('number');
  expect(typeof data.size).toBe('number');
  expect(typeof data.pages).toBe('number');
}

function assertProductShape(item) {
  expect(item).toHaveProperty('id');
  expect(item).toHaveProperty('name');
  expect(item).toHaveProperty('price');
  expect(item).toHaveProperty('sku');
  expect(Array.isArray(item.category)).toBe(true);
}

function assertBasketItemShape(item) {
  expect(item).toHaveProperty('product_id');
  expect(item).toHaveProperty('quantity');
  expect(item).toHaveProperty('price');
  expect(item).toHaveProperty('product_name');
}

function assertOrderShape(order) {
  expect(order).toHaveProperty('id');
  expect(order).toHaveProperty('order_name');
  expect(Array.isArray(order.items)).toBe(true);
}

module.exports = {
  authenticate,
  assertPaginatedShape,
  assertProductShape,
  assertBasketItemShape,
  assertOrderShape,
};
