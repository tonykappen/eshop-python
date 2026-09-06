const { USERS } = require('./constants');
const { loginViaAPI } = require('./auth');

async function addFirstProductToCart(page) {
  page.once('dialog', (dialog) => dialog.accept());

  const addItemResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/basket/') &&
      response.request().method() === 'POST',
    { timeout: 60_000 }
  );

  await page.getByRole('button', { name: 'Add to Cart' }).first().click();
  const response = await addItemResponse;
  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`Add to cart failed: ${response.status()} ${body}`);
  }
}

async function waitForBasketReady(page) {
  await page.goto('/basket.html');
  await page.locator('#loading').waitFor({ state: 'hidden', timeout: 60_000 });

  const basketContent = page.locator('#basketContent');
  const emptyBasket = page.locator('#emptyBasket');
  const error = page.locator('#error');

  await Promise.race([
    basketContent.waitFor({ state: 'visible', timeout: 60_000 }),
    emptyBasket.waitFor({ state: 'visible', timeout: 60_000 }),
    error.waitFor({ state: 'visible', timeout: 60_000 }),
  ]);

  if (await error.isVisible()) {
    const message = (await error.textContent())?.trim() || 'unknown basket error';
    throw new Error(`Basket page error: ${message}`);
  }

  if (await emptyBasket.isVisible()) {
    throw new Error('Basket is empty after adding a product to cart');
  }

  await basketContent.waitFor({ state: 'visible', timeout: 5_000 });
}

async function fillCheckoutForm(page) {
  await page.locator('#firstName').fill('Test');
  await page.locator('#lastName').fill('User');
  await page.locator('#email').fill('test@example.com');
  await page.locator('#addressLine').fill('123 Test Street');
  await page.locator('#country').fill('USA');
  await page.locator('#state').fill('CA');
  await page.locator('#zipCode').fill('94105');
  await page.locator('#cardName').fill('Test User');
  await page.locator('#cardNumber').fill('4111111111111111');
  await page.locator('#expiration').fill('12/30');
  await page.locator('#cvv').fill('123');
}

async function checkoutBasket(page) {
  await page.locator('#checkoutBtn').click();
  await page.locator('#checkoutForm').waitFor({ state: 'visible' });
  await fillCheckoutForm(page);

  page.once('dialog', (dialog) => dialog.accept());

  const checkoutResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/checkout') &&
      response.request().method() === 'POST' &&
      response.ok(),
    { timeout: 60_000 }
  );

  await page.locator('#checkoutFormElement button[type="submit"]').click();
  await checkoutResponse;
  await page.waitForURL('**/orders.html', { timeout: 60_000 });
}

async function loginAndCheckoutOrder(page, request, username = USERS.user) {
  await loginViaAPI(page, request, { username });
  await addFirstProductToCart(page);
  await waitForBasketReady(page);
  await checkoutBasket(page);
}

module.exports = {
  addFirstProductToCart,
  fillCheckoutForm,
  checkoutBasket,
  waitForBasketReady,
  loginAndCheckoutOrder,
};
