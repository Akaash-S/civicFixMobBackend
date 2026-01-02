#!/usr/bin/env python3
"""
Check server environment configuration
"""

import requests

def check_server_config():
    """Check if server has proper configuration"""
    
    print("🔍 Checking Server Configuration")
    print("=" * 40)
    
    base_url = "https://civicfix-server.asolvitra.tech"
    
    # Test health endpoint to see what's configured
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running")
            print(f"   Version: {data.get('version', 'unknown')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                if status == 'healthy':
                    print(f"   ✅ {service}: {status}")
                else:
                    print(f"   ❌ {service}: {status}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    return True

def main():
    if check_server_config():
        print("\n" + "=" * 40)
        print("🔧 Next Steps:")
        print("1. SSH into your EC2 instance")
        print("2. Check if SUPABASE_JWT_SECRET is set:")
        print("   echo $SUPABASE_JWT_SECRET")
        print("3. If not set, add it to your .env file or export it:")
        print("   export SUPABASE_JWT_SECRET='your_secret_here'")
        print("4. Restart your backend application")
        print("5. Run the authentication test again")

if __name__ == "__main__":
    main()