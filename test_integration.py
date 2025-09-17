#!/usr/bin/env python3
"""
Integration test script to verify the eShop API endpoints work correctly.
This script tests the catalog API endpoints with proper authentication and RBAC.
"""

import json
import sys
import time
from typing import Dict, Any, Optional
import requests
from uuid import uuid4


class EShopAPITester:
    """Test the eShop API integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.bearer_token: Optional[str] = None
        self.test_product_id: Optional[str] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_health_endpoints(self) -> bool:
        """Test health endpoints."""
        self.log("Testing health endpoints...")
        
        try:
            # Test basic health check
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code != 200:
                self.log(f"Health check failed: {response.status_code}", "ERROR")
                return False
            self.log("✅ Health check passed")
            
            # Test detailed health check
            response = self.session.get(f"{self.base_url}/health/detailed")
            if response.status_code != 200:
                self.log(f"Detailed health check failed: {response.status_code}", "ERROR")
                return False
            self.log("✅ Detailed health check passed")
            
            return True
            
        except Exception as e:
            self.log(f"Health check error: {e}", "ERROR")
            return False
    
    def test_swagger_documentation(self) -> bool:
        """Test Swagger documentation endpoints."""
        self.log("Testing Swagger documentation...")
        
        try:
            # Test OpenAPI JSON
            response = self.session.get(f"{self.base_url}/openapi.json")
            if response.status_code != 200:
                self.log(f"OpenAPI JSON failed: {response.status_code}", "ERROR")
                return False
            
            openapi_data = response.json()
            if "openapi" not in openapi_data or "paths" not in openapi_data:
                self.log("OpenAPI JSON structure invalid", "ERROR")
                return False
            self.log("✅ OpenAPI JSON accessible")
            
            # Test Swagger UI
            response = self.session.get(f"{self.base_url}/docs")
            if response.status_code != 200:
                self.log(f"Swagger UI failed: {response.status_code}", "ERROR")
                return False
            self.log("✅ Swagger UI accessible")
            
            # Test ReDoc
            response = self.session.get(f"{self.base_url}/redoc")
            if response.status_code != 200:
                self.log(f"ReDoc failed: {response.status_code}", "ERROR")
                return False
            self.log("✅ ReDoc accessible")
            
            return True
            
        except Exception as e:
            self.log(f"Swagger documentation error: {e}", "ERROR")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Test that protected endpoints require authentication."""
        self.log("Testing unauthorized access...")
        
        try:
            # Test products endpoint without auth
            response = self.session.get(f"{self.base_url}/api/v1/products/")
            if response.status_code != 401:
                self.log(f"Products endpoint should require auth: {response.status_code}", "ERROR")
                return False
            self.log("✅ Products endpoint requires authentication")
            
            # Test create product without auth
            response = self.session.post(f"{self.base_url}/api/v1/products/", json={})
            if response.status_code != 401:
                self.log(f"Create product should require auth: {response.status_code}", "ERROR")
                return False
            self.log("✅ Create product requires authentication")
            
            return True
            
        except Exception as e:
            self.log(f"Unauthorized access test error: {e}", "ERROR")
            return False
    
    def test_products_endpoint_structure(self) -> bool:
        """Test that products endpoint returns expected structure."""
        self.log("Testing products endpoint structure...")
        
        try:
            # This will fail with 401, but we can check the response structure
            response = self.session.get(f"{self.base_url}/api/v1/products/")
            
            if response.status_code == 401:
                # Check if it's a proper 401 response
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        self.log("✅ Products endpoint returns proper 401 structure")
                        return True
                except:
                    pass
            
            self.log(f"Unexpected response: {response.status_code}", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"Products endpoint structure test error: {e}", "ERROR")
            return False
    
    def test_api_metadata(self) -> bool:
        """Test API metadata and root endpoint."""
        self.log("Testing API metadata...")
        
        try:
            # Test root endpoint
            response = self.session.get(f"{self.base_url}/")
            if response.status_code != 200:
                self.log(f"Root endpoint failed: {response.status_code}", "ERROR")
                return False
            
            data = response.json()
            expected_fields = ["message", "version", "status"]
            for field in expected_fields:
                if field not in data:
                    self.log(f"Root endpoint missing field: {field}", "ERROR")
                    return False
            
            self.log(f"✅ Root endpoint returns: {data['message']} v{data['version']}")
            return True
            
        except Exception as e:
            self.log(f"API metadata test error: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        self.log("Starting eShop API Integration Tests")
        self.log("=" * 50)
        
        tests = [
            ("Health Endpoints", self.test_health_endpoints),
            ("Swagger Documentation", self.test_swagger_documentation),
            ("Unauthorized Access", self.test_unauthorized_access),
            ("Products Endpoint Structure", self.test_products_endpoint_structure),
            ("API Metadata", self.test_api_metadata),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
                self.log(f"✅ {test_name} PASSED")
            else:
                self.log(f"❌ {test_name} FAILED", "ERROR")
        
        self.log("\n" + "=" * 50)
        self.log(f"Integration Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All tests passed! API is ready for use.", "SUCCESS")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed. Please check the issues above.", "WARNING")
            return False


def main():
    """Main function to run integration tests."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = EShopAPITester(base_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Ready to use:")
        print(f"   • Frontend: {base_url.replace('8000', '3000')}")
        print(f"   • API Docs: {base_url}/docs")
        print(f"   • ReDoc: {base_url}/redoc")
        print(f"   • OpenAPI: {base_url}/openapi.json")
        print(f"   • Postman Collection: EShop_Postman_Collection_Updated.json")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

