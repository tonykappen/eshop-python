const auth = require('../../auth.js');

describe('auth helpers', () => {
  beforeEach(() => {
    localStorage.clear();
    delete window.location;
    window.location = { href: '' };
  });

  describe('getAuthHeaders', () => {
    test('returns empty object when no token', () => {
      expect(auth.getAuthHeaders()).toEqual({});
    });

    test('returns Bearer header when token exists', () => {
      localStorage.setItem('access_token', 'test-token');
      expect(auth.getAuthHeaders()).toEqual({
        Authorization: 'Bearer test-token',
      });
    });
  });

  describe('handleUnauthorized', () => {
    test('clears storage and redirects to login', () => {
      localStorage.setItem('access_token', 'old-token');
      localStorage.setItem('username', 'user');

      auth.handleUnauthorized();

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('username')).toBeNull();
      expect(window.location.href).toBe('index.html');
    });

    test('includes session_expired params when detail provided', () => {
      auth.handleUnauthorized('token expired');

      expect(window.location.href).toContain('session_expired=1');
      expect(window.location.href).toContain('reason=token');
    });
  });

  describe('validateStoredToken', () => {
    test('returns false when no token stored', async () => {
      const result = await auth.validateStoredToken('http://localhost:8000');
      expect(result).toBe(false);
    });

    test('returns true when backend accepts token', async () => {
      localStorage.setItem('access_token', 'valid-token');
      global.fetch = jest.fn().mockResolvedValue({ status: 200, ok: true });

      const result = await auth.validateStoredToken('http://localhost:8000');

      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/me',
        { headers: { Authorization: 'Bearer valid-token' } }
      );
    });

    test('clears storage and returns false on 401', async () => {
      localStorage.setItem('access_token', 'stale-token');
      global.fetch = jest.fn().mockResolvedValue({ status: 401, ok: false });

      const result = await auth.validateStoredToken('http://localhost:8000');

      expect(result).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    test('returns false on network error', async () => {
      localStorage.setItem('access_token', 'token');
      global.fetch = jest.fn().mockRejectedValue(new Error('network'));

      const result = await auth.validateStoredToken('http://localhost:8000');

      expect(result).toBe(false);
    });
  });

  describe('handleUnauthorizedResponse', () => {
    test('redirects with parsed detail', async () => {
      const response = {
        json: () => Promise.resolve({ detail: 'token expired' }),
      };
      auth.handleUnauthorizedResponse(response);
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(window.location.href).toContain('session_expired=1');
    });
  });

  describe('showSessionExpiredMessage', () => {
    test('shows stale signing key message', () => {
      delete window.location;
      window.location = { search: '?session_expired=1&reason=stale_signing_key' };
      document.body.innerHTML = '<div id="error"></div>';
      auth.showSessionExpiredMessage();
      expect(document.getElementById('error').textContent).toContain('sign-in key');
    });
  });
});
