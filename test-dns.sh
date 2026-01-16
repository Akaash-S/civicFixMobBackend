#!/bin/bash

# Quick DNS test script

DOMAIN="civicfix-server.asolvitra.tech"

echo "Testing DNS resolution for: $DOMAIN"
echo ""

# Method 1: nslookup
echo "Method 1: nslookup"
RESOLVED_IP=$(nslookup $DOMAIN 2>/dev/null | grep -i "Address:" | grep -v "#" | tail -1 | awk '{print $2}')
if [ -n "$RESOLVED_IP" ]; then
    echo "✅ Resolved to: $RESOLVED_IP"
else
    echo "❌ Failed"
fi
echo ""

# Method 2: dig
echo "Method 2: dig"
RESOLVED_IP=$(dig +short $DOMAIN 2>/dev/null | head -1)
if [ -n "$RESOLVED_IP" ]; then
    echo "✅ Resolved to: $RESOLVED_IP"
else
    echo "❌ Failed (dig might not be installed)"
fi
echo ""

# Method 3: host
echo "Method 3: host"
RESOLVED_IP=$(host $DOMAIN 2>/dev/null | grep "has address" | awk '{print $4}')
if [ -n "$RESOLVED_IP" ]; then
    echo "✅ Resolved to: $RESOLVED_IP"
else
    echo "❌ Failed (host might not be installed)"
fi
echo ""

# Check if IP is valid format
if [[ "$RESOLVED_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "✅ DNS is working correctly!"
    echo "Your domain resolves to: $RESOLVED_IP"
else
    echo "❌ DNS resolution failed or returned invalid IP"
fi
