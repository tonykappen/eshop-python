/**
 * Shared DOM and formatting utilities for eShop frontend pages.
 */

function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map(function (c) {
                    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                })
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

function resolveUserRole(token) {
    const tokenData = parseJwt(token);
    if (!tokenData || !tokenData.realm_access || !tokenData.realm_access.roles) {
        return 'user';
    }
    const roles = tokenData.realm_access.roles;
    if (roles.includes('admin')) {
        return 'admin';
    }
    if (roles.includes('manager')) {
        return 'manager';
    }
    return 'user';
}

function canManageProducts(userRole) {
    return userRole === 'admin' || userRole === 'manager';
}

function isValidUuid(value) {
    const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(String(value));
}

function calculateBasketSubtotal(items) {
    if (!items || !items.length) {
        return 0;
    }
    return items.reduce(function (sum, item) {
        const price = parseFloat(item.price) || 0;
        const quantity = parseInt(item.quantity, 10) || 1;
        return sum + price * quantity;
    }, 0);
}

function buildPaginationLabel(page, totalPages, totalCount) {
    return `Page ${page} of ${totalPages} (${totalCount} total products)`;
}

const FIELD_NAME_MAP = {
    picture_url: 'productImage',
    name: 'productName',
    description: 'productDescription',
    price: 'productPrice',
    category: 'category',
};

function groupValidationErrors(validationErrors) {
    const errorsByField = {};
    const summaryErrors = [];

    (validationErrors || []).forEach(function (error) {
        const fieldName = error.field || 'unknown';
        const message = error.message || 'Validation error';
        const frontendFieldName = FIELD_NAME_MAP[fieldName] || fieldName;
        if (!errorsByField[frontendFieldName]) {
            errorsByField[frontendFieldName] = [];
        }
        errorsByField[frontendFieldName].push(message);
        summaryErrors.push(`${fieldName}: ${message}`);
    });

    return { errorsByField, summaryErrors };
}

function getProductActionsHtml(product, userRole, escapeFn) {
    const esc = escapeFn || escapeHtml;
    let productId = product.id;
    if (!productId) {
        return '<span style="color: red;">Error: Product ID missing</span>';
    }
    productId = String(productId);
    if (!isValidUuid(productId)) {
        return '<span style="color: red;">Error: Invalid Product ID</span>';
    }

    const productName = product.name || 'Product';
    const productPrice = product.price || 0;

    if (canManageProducts(userRole)) {
        return (
            `<button class="btn-edit" onclick="editProduct('${productId}')">Edit</button>` +
            `<button class="btn-delete" onclick="deleteProduct('${productId}')">Delete</button>`
        );
    }

    const escapedName = esc(productName).replace(/'/g, '&#39;');
    return `<button class="btn-add-cart" onclick="addToCart('${productId}', '${escapedName}', ${productPrice})">Add to Cart</button>`;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        escapeHtml,
        parseJwt,
        resolveUserRole,
        canManageProducts,
        isValidUuid,
        calculateBasketSubtotal,
        buildPaginationLabel,
        groupValidationErrors,
        getProductActionsHtml,
        FIELD_NAME_MAP,
    };
}

if (typeof window !== 'undefined') {
    window.escapeHtml = escapeHtml;
    window.parseJwt = parseJwt;
    window.resolveUserRole = resolveUserRole;
    window.canManageProducts = canManageProducts;
    window.isValidUuid = isValidUuid;
    window.calculateBasketSubtotal = calculateBasketSubtotal;
    window.buildPaginationLabel = buildPaginationLabel;
    window.groupValidationErrors = groupValidationErrors;
    window.getProductActionsHtml = getProductActionsHtml;
    window.FIELD_NAME_MAP = FIELD_NAME_MAP;
}
