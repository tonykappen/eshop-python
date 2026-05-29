const { test, expect } = require('@playwright/test');
const {
  authenticate,
  assertOrderShape,
  assertPaginatedShape,
} = require('./helpers');
const { USERS } = require('../../e2e/helpers/constants');

test.describe('Orders API contracts', () => {
  test('GET /api/v1/orders returns orders wrapper with pagination', async ({ request }) => {
    const headers = await authenticate(request, USERS.user);
    const response = await request.get('/api/v1/orders?page_index=0&page_size=10', { headers });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('orders');
    assertPaginatedShape(data.orders);
  });

  test('order items include required fields when orders exist', async ({ request }) => {
    const headers = await authenticate(request, USERS.user);
    const response = await request.get('/api/v1/orders?page_index=0&page_size=10', { headers });
    const data = await response.json();

    if (data.orders.items.length === 0) {
      test.skip();
    }

    assertOrderShape(data.orders.items[0]);
  });

  test('GET /api/v1/orders/{id} returns order object', async ({ request }) => {
    const headers = await authenticate(request, USERS.user);
    const listResponse = await request.get('/api/v1/orders?page_index=0&page_size=10', { headers });
    const listData = await listResponse.json();

    if (listData.orders.items.length === 0) {
      test.skip();
    }

    const orderId = listData.orders.items[0].id;
    const detailResponse = await request.get(`/api/v1/orders/${orderId}`, { headers });

    expect(detailResponse.ok()).toBeTruthy();
    const detailData = await detailResponse.json();
    expect(detailData).toHaveProperty('order');
    assertOrderShape(detailData.order);
  });
});
