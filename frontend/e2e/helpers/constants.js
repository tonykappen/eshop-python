module.exports = {
  E2E_BASE_URL: process.env.E2E_BASE_URL || 'http://localhost:3000',
  E2E_API_URL: process.env.E2E_API_URL || 'http://localhost:8000',
  E2E_USER_PASSWORD: process.env.E2E_USER_PASSWORD || 'changeme123',
  USERS: {
    user: 'testuser',
    manager: 'manager',
    admin: 'adminuser',
  },
  TIMEOUT: 30_000,
};
