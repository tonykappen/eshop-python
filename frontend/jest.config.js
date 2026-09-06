/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/tests/unit/**/*.test.js'],
  clearMocks: true,
  collectCoverageFrom: [
    'auth.js',
    'config.js',
    'js/**/*.js',
  ],
  coverageDirectory: 'coverage',
  coverageThreshold: {
    global: {
      lines: 80,
    },
  },
};
