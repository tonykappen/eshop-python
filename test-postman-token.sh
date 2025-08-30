#!/bin/bash

echo "🧪 Testing Postman Token Generation..."

# Get a fresh token
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/eshop/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password&grant_type=password&client_id=eshop-api&client_secret=your-client-secret")

# Extract token
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✅ Token generation works!"
    
    # Test the token with API
    API_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/products/)
    
    if echo "$API_RESPONSE" | jq -e '.success' > /dev/null; then
        echo "✅ API call with token works!"
        echo "📊 Products returned: $(echo "$API_RESPONSE" | jq '.data | length')"
    else
        echo "❌ API call failed"
        echo "Response: $API_RESPONSE"
    fi
else
    echo "❌ Token generation failed"
    echo "Response: $TOKEN_RESPONSE"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Import EShop_Postman_Collection.json into Postman"
echo "2. Run any request - it will automatically generate tokens!"
echo "3. Check the console for token generation logs"


