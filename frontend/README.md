# eShop Frontend

A simple HTML/JavaScript frontend for the eShop application.

## Features

- User authentication with Keycloak
- Product listing with pagination
- Role-based access control (RBAC)
- Admin product creation
- Responsive design

## Pages

### 1. Login Page (`index.html`)
- Username/password authentication
- Quick login buttons for test users
- Automatic redirect if already logged in

### 2. Products Page (`products.html`)
- Display all products in a grid layout
- Show user role and permissions
- Admin/Manager can create new products
- Logout functionality

## User Roles

- **User**: Can view products only
- **Manager**: Can view and create products
- **Admin**: Can view and create products (inherits manager + user roles)

## Test Users

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| testuser | password | user | Read-only access to products |
| admin    | password | admin | Full access (view + create products) |

## Usage

1. Start the backend services (PostgreSQL, Keycloak, FastAPI)
2. Open `index.html` in a web browser
3. Login with one of the test users
4. Browse products and test role-based features

## API Integration

The frontend communicates with:
- **Keycloak** (port 8080): Authentication and JWT tokens
- **FastAPI Backend** (port 8000): Product APIs

## Security Features

- JWT token-based authentication
- Role-based UI elements (create button only shown to admin/manager)
- Automatic logout on token expiration
- Secure token storage in localStorage

## Styling

- Clean, modern CSS design
- Responsive grid layout
- Modal dialogs for forms
- Loading and error states
- Role-based visual indicators
