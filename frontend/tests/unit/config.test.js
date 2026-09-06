describe('config.js', () => {
  beforeEach(() => {
    document.head.innerHTML = '';
    delete window.APP_CONFIG;
    jest.resetModules();
  });

  test('sets default APP_CONFIG values', () => {
    require('../../config.js');

    expect(window.APP_CONFIG.API_BASE).toBe('http://localhost:8000');
    expect(window.APP_CONFIG.KEYCLOAK_SERVER_URL).toBe('http://localhost:8080');
    expect(window.APP_CONFIG.KEYCLOAK_REALM).toBe('eshop');
    expect(window.APP_CONFIG.KEYCLOAK_CLIENT_ID).toBe('eshop-api');
  });

  test('overrides values from meta tags', () => {
    const apiMeta = document.createElement('meta');
    apiMeta.setAttribute('name', 'api-base');
    apiMeta.setAttribute('content', 'http://api.example.com');
    document.head.appendChild(apiMeta);

    const realmMeta = document.createElement('meta');
    realmMeta.setAttribute('name', 'keycloak-client-id');
    realmMeta.setAttribute('content', 'custom-client');
    document.head.appendChild(realmMeta);

    require('../../config.js');

    expect(window.APP_CONFIG.API_BASE).toBe('http://api.example.com');
    expect(window.APP_CONFIG.KEYCLOAK_CLIENT_ID).toBe('custom-client');
  });

  test('exports config via module.exports in Node', () => {
    const config = require('../../config.js');

    expect(config.API_BASE).toBe('http://localhost:8000');
    expect(config.KEYCLOAK_REALM).toBe('eshop');
  });
});
