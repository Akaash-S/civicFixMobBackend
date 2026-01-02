#!/bin/bash

# Quick API Test Script for CivicFix
# Simple tests for the most important endpoints

BASE_URL="https://civicfix-server.asolvitra.tech"

echo "🚀 Quick API Test for CivicFix"
echo "=============================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Basic connectivity and health
echo "1. Testing basic connectivity..."
curl -s "$BASE_URL/health" | python3 -m json.tool || echo "❌ Health check failed"
echo ""

# Test 2: Home endpoint
echo "2. Testing home endpoint..."
curl -s "$BASE_URL/" | python3 -m json.tool || echo "❌ Home endpoint failed"
echo ""

# Test 3: Get all issues
echo "3. Testing issues endpoint..."
curl -s "$BASE_URL/api/v1/issues" | python3 -m json.tool | head -20
echo ""

# Test 4: Get categories
echo "4. Testing categories endpoint..."
curl -s "$BASE_URL/api/v1/categories" | python3 -m json.tool
echo ""

# Test 5: Get system stats
echo "5. Testing stats endpoint..."
curl -s "$BASE_URL/api/v1/stats" | python3 -m json.tool
echo ""

# Test 6: Test HTTPS redirect
echo "6. Testing HTTP to HTTPS redirect..."
curl -I "http://civicfix-server.asolvitra.tech/" 2>/dev/null | head -1
echo ""

echo "✅ Quick test complete!"
echo ""
echo "🔗 Try these URLs in your browser:"
echo "   • $BASE_URL/"
echo "   • $BASE_URL/health"
echo "   • $BASE_URL/api/v1/issues"
echo "   • $BASE_URL/api/v1/categories"