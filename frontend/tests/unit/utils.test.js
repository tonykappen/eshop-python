const utils = require('../../js/utils.js');
const apiClient = require('../../js/api-client.js');

describe('utils', () => {
  test('escapeHtml escapes angle brackets', () => {
    expect(utils.escapeHtml('<script>')).toBe('&lt;script&gt;');
    expect(utils.escapeHtml(null)).toBe('');
  });

  test('parseJwt decodes payload roles', () => {
    const header = btoa(JSON.stringify({ alg: 'none' }));
    const payload = btoa(
      JSON.stringify({ realm_access: { roles: ['admin', 'user'] } })
    );
    const token = `${header}.${payload}.sig`;
    expect(utils.resolveUserRole(token)).toBe('admin');
  });

  test('isValidUuid validates format', () => {
    expect(utils.isValidUuid('123e4567-e89b-12d3-a456-426614174000')).toBe(true);
    expect(utils.isValidUuid('not-a-uuid')).toBe(false);
  });

  test('calculateBasketSubtotal sums item totals', () => {
    const total = utils.calculateBasketSubtotal([
      { price: '10.00', quantity: 2 },
      { price: 5, quantity: 1 },
    ]);
    expect(total).toBe(25);
  });

  test('groupValidationErrors maps backend fields', () => {
    const grouped = utils.groupValidationErrors([
      { field: 'name', message: 'required' },
      { field: 'price', message: 'invalid' },
    ]);
    expect(grouped.errorsByField.productName).toEqual(['required']);
    expect(grouped.summaryErrors[0]).toContain('name');
  });

  test('getProductActionsHtml renders cart button for user', () => {
    const html = utils.getProductActionsHtml(
      { id: '123e4567-e89b-12d3-a456-426614174000', name: 'Widget', price: 9.99 },
      'user',
      utils.escapeHtml
    );
    expect(html).toContain('Add to Cart');
    expect(html).toContain('123e4567-e89b-12d3-a456-426614174000');
  });

  test('getProductActionsHtml renders edit/delete for manager', () => {
    const html = utils.getProductActionsHtml(
      { id: '123e4567-e89b-12d3-a456-426614174000', name: 'Widget', price: 9.99 },
      'manager',
      utils.escapeHtml
    );
    expect(html).toContain('Edit');
    expect(html).toContain('Delete');
  });
});

describe('api-client', () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = jest.fn();
  });

  test('createApiClient attaches bearer token', async () => {
    localStorage.setItem('access_token', 'abc');
    fetch.mockResolvedValue({ status: 200, ok: true });

    const client = apiClient.createApiClient({ apiBase: 'http://localhost:8000' });
    await client.get('/api/v1/products/');

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/products/',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer abc' }),
      })
    );
  });

  test('createApiClient invokes unauthorized handler on 401', async () => {
    const onUnauthorized = jest.fn();
    fetch.mockResolvedValue({ status: 401, ok: false });

    const client = apiClient.createApiClient({
      apiBase: 'http://localhost:8000',
      onUnauthorized,
    });
    await client.get('/api/v1/basket/user');

    expect(onUnauthorized).toHaveBeenCalled();
  });

  test('createApiClient post and delete helpers', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true });
    const client = apiClient.createApiClient({ apiBase: 'http://localhost:8000' });

    await client.post('/api/v1/basket/user/items', { quantity: 1 });
    await client.delete('/api/v1/basket/user');

    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[0][1].method).toBe('POST');
    expect(fetch.mock.calls[1][1].method).toBe('DELETE');
  });
});
