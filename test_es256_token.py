#!/usr/bin/env python3
"""
Test ES256 Token Handling
Test how to handle Supabase ES256 tokens
"""

import jwt
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_es256_token():
    """Test ES256 token handling"""
    
    backend_url = "https://civicfix-server.asolvitra.tech"
    
    print("🔍 Testing ES256 Token Handling")
    print("=" * 50)
    
    # Create a sample ES256-like token (we'll decode without verification)
    # This simulates what Supabase sends
    sample_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY2OTQ4MDAwLCJpYXQiOjE3NjY5NDQ0MDAsImlzcyI6Imh0dHBzOi8veW91ci1wcm9qZWN0LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJ0ZXN0LXVzZXItMTIzNDUiLCJlbWFpbCI6InRlc3R1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20iLCJmdWxsX25hbWUiOiJUZXN0IFVzZXIifX0"
    
    print("🔍 Analyzing token without verification...")
    try:
        # Decode without verification to see the payload
        unverified = jwt.decode(sample_token, options={"verify_signature": False})
        header = jwt.get_unverified_header(sample_token)
        
        print(f"📋 Token Header:")
        for key, value in header.items():
            print(f"   {key}: {value}")
        
        print(f"\n📋 Token Payload:")
        for key, value in unverified.items():
            if key != 'user_metadata':
                print(f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        
        print(f"\n✅ Token can be decoded without signature verification")
        
        # Test with server using the updated backend
        print(f"\n🌐 Testing with server...")
        headers = {
            'Authorization': f'Bearer {sample_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{backend_url}/api/v1/auth/test", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Server accepted ES256 token!")
        else:
            print("❌ Server still rejecting token")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("ES256 tokens require special handling:")
    print("1. Cannot verify signature without public key")
    print("2. Can decode payload without verification")
    print("3. Should validate payload fields manually")

if __name__ == "__main__":
    test_es256_token()