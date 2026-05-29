const { test, expect } = require('@playwright/test');
const {
  authenticate,
  assertPaginatedShape,
  assertProductShape,
} = require('./helpers');

test.describe('Products API contracts', () => {
  test('GET /api/v1/products returns paginated product list', async ({ request }) => {
    const headers = await authenticate(request);
    const response = await request.get('/api/v1/products/?page=1&page_size=10', { headers });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    assertPaginatedShape(data);
    expect(data.items.length).toBeGreaterThan(0);
    assertProductShape(data.items[0]);
  });

  test('GET /api/v1/products with search_term returns items array', async ({ request }) => {
    const headers = await authenticate(request);
    const listResponse = await request.get('/api/v1/products/?page=1&page_size=1', { headers });
    const listData = await listResponse.json();
    const searchTerm = listData.items[0]?.name?.split(' ')[0] || 'product';

    const response = await request.get(
      `/api/v1/products/?page=1&page_size=10&search_term=${encodeURIComponent(searchTerm)}`,
      { headers }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    assertPaginatedShape(data);
  });

  test('GET /api/v1/products without auth returns 401', async ({ request }) => {
    const response = await request.get('/api/v1/products/?page=1&page_size=10');
    expect(response.status()).toBe(401);
  });
});
