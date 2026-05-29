#!/bin/bash

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo "Setting up frontend test prerequisites..."

if ! command -v node >/dev/null 2>&1; then
    echo "Node.js is required. Install Node.js 20+ and retry."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required. Install Node.js 20+ and retry."
    exit 1
fi

echo "Node $(node -v), npm $(npm -v)"

cd "${FRONTEND_DIR}"

echo "Installing npm dependencies..."
npm ci

echo "Installing Playwright Chromium..."
if [[ "$(uname -s)" == "Linux" ]]; then
    npx playwright install --with-deps chromium
else
    npx playwright install chromium
fi

echo ""
echo "Frontend test prerequisites installed successfully!"
echo ""
echo "Next steps:"
echo "  Unit tests:         cd frontend && npm test"
echo "  API contract tests: cd frontend && npm run test:api-contracts"
echo "  E2E tests:          cd frontend && npm run test:e2e"
echo ""
echo "API contract and E2E tests require the full stack:"
echo "  docker compose up -d --wait"
echo ""
echo "See docs/TESTING.md for details."
