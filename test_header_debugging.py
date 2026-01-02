#!/usr/bin/env python3
"""
Header Debugging Test
Tests exactly what headers are being sent and received through nginx
"""

import requests
import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_test_token():
    """Create a test JWT token"""
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    current_time = int(time.time())
    
    payload = {
        'aud': 'authenticated',
        'exp': current_time + 3600,
        'iat': current_time,
        'iss': 'https://your-project.supabase.co/auth/v1',
        'sub': 'debug-test-user',
        'email': 'debug@example.com',
        'role': 'authenticated',
        'user_metadata': {
            'email': 'debug@example.com',
            'full_name': 'Debug Test User'
        }
    }
    
    return jwt.encode(payload, jwt_secret, algorithm='HS256')

def test_header_preservation():
    """Test what headers nginx is actually sending"""
    
    print("🔍 Header Debugging Test")
    print("=" * 50)
    
    token = create_test_token()
    nginx_url = "https://civicfix-server.asolvitra.tech"
    
    # Test cases with different header formats
    test_cases = [
        ("Normal header", f'Bearer {token}'),
        ("Trailing space", f'Bearer {token} '),
        ("Two trailing spaces", f'Bearer {token}  '),
        ("Multiple spaces", f'Bearer  {token}'),
        ("Tab character", f'Bearer\t{token}'),
    ]
    
    print(f"🔑 Test Token: {token[:30]}...")
    print(f"🌐 Testing URL: {nginx_url}")
    
    for test_name, auth_header in test_cases:
        print(f"\n📋 Testing: {test_name}")
        print(f"   Sending: {repr(auth_header)}")
        print(f"   Length: {len(auth_header)}")
        print(f"   Ends with space: {auth_header.endswith(' ')}")
        print(f"   Raw bytes: {[ord(c) for c in auth_header[-5:]]}")  # Last 5 chars
        
        headers = {'Authorization': auth_header}
        
        try:
            # Test the debug endpoint if available
            debug_response = requests.get(f"{nginx_url}/debug-headers", headers=headers, timeout=5)
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                received_auth = debug_data.get('authorization_header', 'NOT_FOUND')
                print(f"   Received: {received_auth}")
                print(f"   Received length: {debug_data.get('authorization_length', 0)}")
                print(f"   Received ends with space: {debug_data.get('authorization_ends_with_space', False)}")
                
                # Compare sent vs received
                if repr(auth_header) == received_auth:
                    print(f"   ✅ Header preserved exactly")
                else:
                    print(f"   ❌ Header modified by nginx")
                    print(f"      Original: {repr(auth_header)}")
                    print(f"      Received: {received_auth}")
            else:
                print(f"   ⚠️ Debug endpoint not available (status: {debug_response.status_code})")
                
            # Test the actual auth endpoint
            auth_response = requests.get(f"{nginx_url}/api/v1/auth/test", headers=headers, timeout=5)
            print(f"   Auth endpoint: {auth_response.status_code}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 Analysis:")
    print("- Compare 'Sending' vs 'Received' to see nginx modifications")
    print("- If headers are modified, nginx config needs adjustment")
    print("- If headers are preserved but auth fails, backend logic needs adjustment")

if __name__ == "__main__":
    test_header_preservation()