const { test, expect } = require('@playwright/test');
const { authenticate } = require('./helpers');
const { USERS } = require('../../e2e/helpers/constants');

test.describe('API error response contracts', () => {
  test('GET /api/v1/products/{id} returns 404 for unknown product', async ({ request }) => {
    const headers = await authenticate(request);
    const response = await request.get(
      '/api/v1/products/00000000-0000-0000-0000-000000000099',
      { headers }
    );
    expect(response.status()).toBe(404);
  });

  test('POST /api/v1/products returns 422 for invalid payload', async ({ request }) => {
    const headers = await authenticate(request, USERS.admin);
    const response = await request.post('/api/v1/products/', {
      headers: { ...headers, 'Content-Type': 'application/json' },
      data: { name: '', description: '', price: -1, category: [] },
    });
    expect([400, 422]).toContain(response.status());
  });

  test('GET /api/v1/basket/{user} without auth returns 401', async ({ request }) => {
    const response = await request.get('/api/v1/basket/test-user');
    expect(response.status()).toBe(401);
  });

  test('GET /api/v1/orders without auth returns 401', async ({ request }) => {
    const response = await request.get('/api/v1/orders?page=1&page_size=10');
    expect(response.status()).toBe(401);
  });
});
