const { test, expect } = require('@playwright/test');
const {
  authenticate,
  assertBasketItemShape,
  assertPaginatedShape,
  assertProductShape,
} = require('./helpers');
const { USERS } = require('../../e2e/helpers/constants');

test.describe('Basket API contracts', () => {
  test('GET basket returns shopping_cart shape or 404 when empty', async ({ request }) => {
    const headers = await authenticate(request, USERS.user);
    const response = await request.get(`/api/v1/basket/${USERS.user}`, { headers });

    expect([200, 404]).toContain(response.status());
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toHaveProperty('shopping_cart');
      expect(data.shopping_cart).toHaveProperty('user_name', USERS.user);
      expect(Array.isArray(data.shopping_cart.items)).toBe(true);
    }
  });

  test('POST item then GET basket includes item fields', async ({ request }) => {
    const headers = await authenticate(request, USERS.user);

    const productsResponse = await request.get('/api/v1/products/?page=1&page_size=1', { headers });
    expect(productsResponse.ok()).toBeTruthy();
    const productsData = await productsResponse.json();
    assertPaginatedShape(productsData);
    const product = productsData.items[0];
    assertProductShape(product);

    const addResponse = await request.post(`/api/v1/basket/${USERS.user}/items`, {
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      data: {
        shopping_cart_item: {
          id: null,
          shopping_cart_id: null,
          product_id: product.id,
          quantity: 1,
          color: 'Default',
          price: product.price,
          product_name: product.name,
        },
      },
    });

    expect([200, 201]).toContain(addResponse.status());
    const addData = await addResponse.json();
    expect(addData).toHaveProperty('id');

    const basketResponse = await request.get(`/api/v1/basket/${USERS.user}`, { headers });
    expect(basketResponse.ok()).toBeTruthy();
    const basketData = await basketResponse.json();
    expect(basketData.shopping_cart.items.length).toBeGreaterThan(0);

    const item = basketData.shopping_cart.items.find(
      (entry) => String(entry.product_id) === String(product.id)
    );
    expect(item).toBeTruthy();
    assertBasketItemShape(item);
  });
});
