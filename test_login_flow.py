#!/usr/bin/env python3
"""
Test the login flow to see what's happening with authentication.
"""

import requests
import json
import time

def test_login_flow():
    """Test the complete login flow."""
    base_url = "http://localhost:8000"
    
    print("🔐 Testing eShop Login Flow")
    print("=" * 50)
    
    # Step 1: Test health
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Step 2: Test token endpoint
    print("\n2. Testing token endpoint...")
    try:
        token_response = requests.post(
            f"{base_url}/api/v1/auth-proxy/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "user",
                "password": "password",
                "grant_type": "password",
                "client_id": "eshop-api",
                "client_secret": "your-client-secret"
            }
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            print("✅ Token obtained successfully")
            print(f"   Token type: {token_data.get('token_type')}")
            print(f"   Expires in: {token_data.get('expires_in')} seconds")
            print(f"   Token preview: {token_data.get('access_token', '')[:50]}...")
            
            access_token = token_data.get('access_token')
        else:
            print(f"❌ Token request failed: {token_response.status_code}")
            print(f"   Response: {token_response.text}")
            return
    except Exception as e:
        print(f"❌ Token request error: {e}")
        return
    
    # Step 3: Test user info endpoint
    print("\n3. Testing user info endpoint...")
    try:
        user_response = requests.get(
            f"{base_url}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print("✅ User info retrieved successfully")
            print(f"   User: {user_data.get('username')}")
            print(f"   Roles: {user_data.get('roles')}")
        else:
            print(f"❌ User info request failed: {user_response.status_code}")
            print(f"   Response: {user_response.text}")
    except Exception as e:
        print(f"❌ User info request error: {e}")
    
    # Step 4: Test products endpoint
    print("\n4. Testing products endpoint...")
    try:
        products_response = requests.get(
            f"{base_url}/api/v1/products/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if products_response.status_code == 200:
            products_data = products_response.json()
            print("✅ Products retrieved successfully")
            print(f"   Total products: {products_data.get('total_count', 0)}")
            print(f"   Products on page: {len(products_data.get('data', []))}")
            print(f"   Page: {products_data.get('page', 1)} of {products_data.get('total_pages', 1)}")
            
            # Show first few products
            products = products_data.get('data', [])
            if products:
                print("\n   First few products:")
                for i, product in enumerate(products[:3]):
                    print(f"     {i+1}. {product.get('name')} - ${product.get('price')}")
        else:
            print(f"❌ Products request failed: {products_response.status_code}")
            print(f"   Response: {products_response.text}")
    except Exception as e:
        print(f"❌ Products request error: {e}")
    
    # Step 5: Test CORS
    print("\n5. Testing CORS...")
    try:
        cors_response = requests.options(
            f"{base_url}/api/v1/products/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization"
            }
        )
        
        if cors_response.status_code == 200:
            print("✅ CORS preflight successful")
            cors_headers = {k: v for k, v in cors_response.headers.items() if 'access-control' in k.lower()}
            if cors_headers:
                print("   CORS headers:")
                for k, v in cors_headers.items():
                    print(f"     {k}: {v}")
        else:
            print(f"❌ CORS preflight failed: {cors_response.status_code}")
    except Exception as e:
        print(f"❌ CORS test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Login flow test completed!")
    print("\nNext steps:")
    print("1. Open http://localhost:3000/products_debug.html in your browser")
    print("2. Check the debug information to see what's happening")
    print("3. If you see 'No token or username found', try logging in again")

if __name__ == "__main__":
    test_login_flow()



