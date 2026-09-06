// @ts-check
const { defineConfig, devices } = require('@playwright/test');

const frontendUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';
const apiUrl = process.env.E2E_API_URL || 'http://localhost:8000';

/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = defineConfig({
  globalSetup: require.resolve('./global-setup.js'),
  outputDir: 'test-results',
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'e2e',
      testDir: 'e2e',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: frontendUrl,
      },
    },
    {
      name: 'api-contracts',
      testDir: 'tests/api-contracts',
      use: {
        baseURL: apiUrl,
      },
    },
  ],
});
