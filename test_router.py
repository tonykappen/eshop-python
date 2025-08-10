#!/usr/bin/env python3
"""Test script to verify router inclusion."""

from fastapi import FastAPI
from app.modules.catalog.api.router import router as catalog_router

# Create a minimal FastAPI app
app = FastAPI()

# Include the catalog router
print("🔧 Including catalog router...")
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
print("✅ Catalog router included successfully")

# Print all routes
print("📋 App routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  - {route.path}")

print("📋 Catalog router routes:")
for route in catalog_router.routes:
    if hasattr(route, 'path'):
        print(f"  - {route.path}")

# Test the endpoint
import uvicorn
import asyncio
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get("/api/v1/test")
print(f"🧪 Test response: {response.status_code} - {response.json()}")
