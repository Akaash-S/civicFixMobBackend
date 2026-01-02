#!/bin/bash

# CivicFix API Endpoint Testing Script
# Tests all major API endpoints on https://civicfix-server.asolvitra.tech

set -e

BASE_URL="https://civicfix-server.asolvitra.tech"
DOMAIN="civicfix-server.asolvitra.tech"

echo "🧪 CivicFix API Endpoint Testing"
echo "================================"
echo "Base URL: $BASE_URL"
echo "Testing started at: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}
    local headers=${5:-""}
    local data=${6:-""}
    
    echo -n "Testing $method $endpoint - $description... "
    
    # Build curl command
    local curl_cmd="curl -s -w '%{http_code}' -o /tmp/response.json"
    
    if [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        curl_cmd="$curl_cmd -X $method"
        if [ -n "$data" ]; then
            curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
        fi
    fi
    
    if [ -n "$headers" ]; then
        curl_cmd="$curl_cmd $headers"
    fi
    
    curl_cmd="$curl_cmd $BASE_URL$endpoint"
    
    # Execute curl command
    local status_code=$(eval $curl_cmd)
    local response=$(cat /tmp/response.json 2>/dev/null || echo "")
    
    # Check result
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($status_code)"
        if [ -n "$response" ] && [ "$response" != "null" ]; then
            echo "   Response: $(echo $response | head -c 100)..."
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        if [ -n "$response" ]; then
            echo "   Response: $response"
        fi
    fi
    echo ""
}

# Function to test with authentication
test_auth_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local token=${4:-""}
    local expected_status=${5:-401}
    local data=${6:-""}
    
    if [ -n "$token" ]; then
        test_endpoint "$method" "$endpoint" "$description (with auth)" "200" "-H 'Authorization: Bearer $token'" "$data"
    else
        test_endpoint "$method" "$endpoint" "$description (no auth)" "$expected_status" "" "$data"
    fi
}

echo "🌐 Basic Connectivity Tests"
echo "============================"

# Test 1: Basic connectivity
test_endpoint "GET" "/" "Home endpoint" "200"

# Test 2: Health check
test_endpoint "GET" "/health" "Health check" "200"

# Test 3: Nginx health check
test_endpoint "GET" "/nginx-health" "Nginx health check" "200"

echo "🔒 SSL/HTTPS Tests"
echo "=================="

# Test SSL certificate
echo -n "Testing SSL certificate... "
ssl_result=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "   $ssl_result"
else
    echo -e "${RED}❌ FAIL${NC}"
fi
echo ""

# Test HTTP to HTTPS redirect
echo -n "Testing HTTP to HTTPS redirect... "
redirect_status=$(curl -s -o /dev/null -w '%{http_code}' http://$DOMAIN/)
if [ "$redirect_status" = "301" ]; then
    echo -e "${GREEN}✅ PASS${NC} (301 redirect)"
else
    echo -e "${RED}❌ FAIL${NC} (Expected: 301, Got: $redirect_status)"
fi
echo ""

echo "📊 Public API Endpoints (No Auth Required)"
echo "=========================================="

# Test 4: Get issues (public)
test_endpoint "GET" "/api/v1/issues" "Get all issues" "200"

# Test 5: Get categories
test_endpoint "GET" "/api/v1/categories" "Get categories" "200"

# Test 6: Get status options
test_endpoint "GET" "/api/v1/status-options" "Get status options" "200"

# Test 7: Get priority options
test_endpoint "GET" "/api/v1/priority-options" "Get priority options" "200"

# Test 8: Get system stats
test_endpoint "GET" "/api/v1/stats" "Get system statistics" "200"

# Test 9: Get nearby issues (with parameters)
test_endpoint "GET" "/api/v1/issues/nearby?lat=12.9716&lng=77.5946&radius=5" "Get nearby issues" "200"

# Test 10: Get specific issue (assuming issue ID 1 exists)
test_endpoint "GET" "/api/v1/issues/1" "Get specific issue" "200"

echo "🔐 Authentication Required Endpoints"
echo "===================================="

# Test 11: Authentication endpoints (should fail without token)
test_auth_endpoint "GET" "/api/v1/users/me" "Get current user"
test_auth_endpoint "GET" "/api/v1/auth/test" "Test authentication"
test_auth_endpoint "POST" "/api/v1/issues" "Create issue"
test_auth_endpoint "POST" "/api/v1/upload" "Upload file"

echo "🧪 Error Handling Tests"
echo "======================="

# Test 12: Non-existent endpoint
test_endpoint "GET" "/api/v1/nonexistent" "Non-existent endpoint" "404"

# Test 13: Invalid issue ID
test_endpoint "GET" "/api/v1/issues/99999" "Invalid issue ID" "404"

# Test 14: Invalid method
test_endpoint "DELETE" "/" "Invalid method on home" "405"

echo "📱 CORS and Headers Tests"
echo "========================"

# Test 15: CORS preflight
echo -n "Testing CORS preflight... "
cors_status=$(curl -s -o /dev/null -w '%{http_code}' -X OPTIONS -H "Origin: https://example.com" -H "Access-Control-Request-Method: GET" $BASE_URL/api/v1/issues)
if [ "$cors_status" = "200" ] || [ "$cors_status" = "204" ]; then
    echo -e "${GREEN}✅ PASS${NC} ($cors_status)"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (Got: $cors_status)"
fi
echo ""

# Test 16: Security headers
echo -n "Testing security headers... "
security_headers=$(curl -s -I $BASE_URL/ | grep -E "(X-Frame-Options|X-Content-Type-Options|X-XSS-Protection)")
if [ -n "$security_headers" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "   $security_headers" | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (No security headers found)"
fi
echo ""

echo "🔍 Performance Tests"
echo "==================="

# Test 17: Response time
echo -n "Testing response time... "
response_time=$(curl -s -o /dev/null -w '%{time_total}' $BASE_URL/health)
if (( $(echo "$response_time < 2.0" | bc -l) )); then
    echo -e "${GREEN}✅ PASS${NC} (${response_time}s)"
else
    echo -e "${YELLOW}⚠️  SLOW${NC} (${response_time}s)"
fi
echo ""

# Test 18: Gzip compression
echo -n "Testing Gzip compression... "
gzip_test=$(curl -s -H "Accept-Encoding: gzip" -I $BASE_URL/ | grep -i "content-encoding: gzip")
if [ -n "$gzip_test" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (Gzip not enabled)"
fi
echo ""

echo "📋 Test Summary"
echo "==============="
echo "Testing completed at: $(date)"
echo ""
echo "🔗 Useful URLs:"
echo "   • Home: $BASE_URL/"
echo "   • Health: $BASE_URL/health"
echo "   • API Base: $BASE_URL/api/v1/"
echo "   • Issues: $BASE_URL/api/v1/issues"
echo "   • Categories: $BASE_URL/api/v1/categories"
echo ""
echo "📚 API Documentation:"
echo "   • All endpoints are accessible via HTTPS"
echo "   • Authentication required for POST/PUT/DELETE operations"
echo "   • Use 'Authorization: Bearer <token>' header for authenticated requests"
echo ""

# Cleanup
rm -f /tmp/response.json

echo "✅ API testing complete!"