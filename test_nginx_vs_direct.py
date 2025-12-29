#!/usr/bin/env python3
"""
Test Nginx vs Direct Backend Access
Compares authentication behavior between nginx proxy and direct backend access
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
        'sub': 'nginx-test-user',
        'email': 'nginxtest@example.com',
        'role': 'authenticated',
        'user_metadata': {
            'email': 'nginxtest@example.com',
            'full_name': 'Nginx Test User'
        }
    }
    
    return jwt.encode(payload, jwt_secret, algorithm='HS256')

def test_endpoint(url, headers, description):
    """Test an endpoint with given headers"""
    try:
        response = requests.get(f"{url}/api/v1/auth/test", headers=headers, timeout=5)
        return response.status_code, response.text[:200]
    except Exception as e:
        return None, str(e)

def compare_nginx_vs_direct():
    """Compare nginx proxy vs direct backend access"""
    
    print("🔍 Nginx vs Direct Backend Authentication Test")
    print("=" * 60)
    
    # URLs
    nginx_url = "http://3.110.42.224:80"  # Through nginx
    direct_url = "http://3.110.42.224:5000"  # Direct to backend (if accessible)
    
    # Create test token
    token = create_test_token()
    print(f"🔑 Test Token: {token[:30]}...")
    
    # Test cases that might be affected by nginx
    test_cases = [
        ("Valid token", {'Authorization': f'Bearer {token}'}),
        ("Trailing space", {'Authorization': f'Bearer {token} '}),
        ("Multiple spaces", {'Authorization': f'Bearer  {token}'}),
        ("Empty Bearer", {'Authorization': 'Bearer '}),
        ("Invalid token", {'Authorization': 'Bearer invalid-token'}),
    ]
    
    print(f"\n📊 Comparison Results:")
    print("-" * 60)
    print(f"{'Test Case':<20} {'Nginx':<15} {'Direct':<15} {'Match':<10}")
    print("-" * 60)
    
    for test_name, headers in test_cases:
        # Test through nginx
        nginx_status, nginx_response = test_endpoint(nginx_url, headers, f"Nginx - {test_name}")
        
        # Test direct backend (may not be accessible from outside)
        direct_status, direct_response = test_endpoint(direct_url, headers, f"Direct - {test_name}")
        
        # Compare results
        if direct_status is None:
            direct_display = "N/A"
            match = "N/A"
        else:
            direct_display = str(direct_status)
            match = "✅" if nginx_status == direct_status else "❌"
        
        nginx_display = str(nginx_status) if nginx_status else "ERROR"
        
        print(f"{test_name:<20} {nginx_display:<15} {direct_display:<15} {match:<10}")
        
        # Show response details for mismatches
        if match == "❌":
            print(f"  Nginx response: {nginx_response}")
            print(f"  Direct response: {direct_response}")
    
    print("-" * 60)
    
    # Test health endpoints
    print(f"\n🏥 Health Check Comparison:")
    
    try:
        nginx_health = requests.get(f"{nginx_url}/health", timeout=5)
        print(f"Nginx Health: {nginx_health.status_code}")
        if nginx_health.status_code == 200:
            health_data = nginx_health.json()
            print(f"  Version: {health_data.get('version', 'unknown')}")
            print(f"  Auth: {health_data.get('authentication', 'unknown')}")
    except Exception as e:
        print(f"Nginx Health Error: {e}")
    
    try:
        direct_health = requests.get(f"{direct_url}/health", timeout=5)
        print(f"Direct Health: {direct_health.status_code}")
        if direct_health.status_code == 200:
            health_data = direct_health.json()
            print(f"  Version: {health_data.get('version', 'unknown')}")
            print(f"  Auth: {health_data.get('authentication', 'unknown')}")
    except Exception as e:
        print(f"Direct Health: Not accessible externally (expected)")
    
    print("\n" + "=" * 60)
    print("🔍 Analysis:")
    print("- If Nginx and Direct results differ, nginx is modifying headers")
    print("- If Direct is not accessible, that's normal (internal port)")
    print("- Focus on fixing nginx configuration to match expected behavior")
    
    return True

if __name__ == "__main__":
    compare_nginx_vs_direct()