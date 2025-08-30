#!/bin/bash

# Get Bearer Token for eShop API
echo "🔐 Getting Bearer Token for eShop API..."

# Get token
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret")

# Extract token using jq
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✅ Bearer Token obtained successfully!"
    echo ""
    echo "🔑 Bearer Token:"
    echo "$TOKEN"
    echo ""
    echo "📋 Usage Examples:"
    echo "curl -H \"Authorization: Bearer $TOKEN\" http://localhost:8000/api/v1/products/"
    echo ""
    echo "🔗 Postman Collection:"
    echo "Import EShop_Postman_Collection.json into Postman"
    echo "The collection will automatically generate tokens!"
else
    echo "❌ Failed to get Bearer Token"
    echo "Response: $TOKEN_RESPONSE"
fi


