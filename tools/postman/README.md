# Postman API Collections

Manual API exploration collections for the eShop backend. These are **not** used in CI.

## Import

1. Open [Postman](https://www.postman.com/downloads/)
2. **Import** → select one or more `.json` files from this folder
3. Set the collection variable `baseUrl` to `http://localhost:8000` (or your backend URL)
4. Run **Login** requests first to obtain a JWT, then call protected endpoints

## Collections

| File | Description |
|------|-------------|
| `EShop_Postman_Collection_Updated.json` | Most complete collection with RBAC test flows |
| `EShop_Postman_Collection.json` | Original collection |
| `EShop_Postman_Collection_Simple.json` | Minimal subset |
| `EShopModules.postman_collection.json` | Per-module endpoints |
| `eShop API Collection.postman_collection.json` | Alternate layout |

## Prerequisites

Start the application stack before sending requests. See [docs/GETTING_STARTED.md](../../docs/GETTING_STARTED.md).
