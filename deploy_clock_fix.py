#!/usr/bin/env python3
"""
Deploy Clock Skew Fix
Quick deployment of the JWT clock skew fix
"""

import subprocess
import sys

def deploy_clock_fix():
    """Deploy the JWT clock skew fix"""
    
    server_ip = "3.110.42.224"
    server_user = "ubuntu"
    project_dir = "/home/ubuntu/civicFix"
    
    print("🔧 Deploying JWT Clock Skew Fix")
    print("=" * 40)
    
    # Copy updated app.py
    print("📁 Copying updated app.py...")
    scp_command = f"scp app.py {server_user}@{server_ip}:{project_dir}/backend/"
    
    try:
        result = subprocess.run(scp_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ File copied successfully")
        else:
            print(f"❌ Copy failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Copy error: {e}")
        return False
    
    # Restart container
    print("\n🔄 Restarting backend container...")
    restart_command = f"""ssh {server_user}@{server_ip} 'cd {project_dir}/backend && docker-compose restart backend'"""
    
    try:
        result = subprocess.run(restart_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Container restarted successfully")
            print(f"Output: {result.stdout}")
        else:
            print(f"❌ Restart failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Restart error: {e}")
        return False
    
    print("\n⏳ Waiting for container to start...")
    import time
    time.sleep(10)
    
    # Test authentication
    print("\n🧪 Testing authentication...")
    try:
        import requests
        import jwt
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
        
        if jwt_secret:
            # Create test token
            payload = {
                'aud': 'authenticated',
                'exp': int(time.time()) + 3600,
                'iat': int(time.time()),
                'iss': 'https://your-project.supabase.co/auth/v1',
                'sub': 'test-user',
                'email': 'test@example.com',
                'role': 'authenticated'
            }
            
            token = jwt.encode(payload, jwt_secret, algorithm='HS256')
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(f"http://{server_ip}/api/v1/auth/test", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ Authentication test passed!")
                data = response.json()
                print(f"   User: {data.get('user', {}).get('email', 'unknown')}")
                return True
            else:
                print(f"❌ Authentication test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        else:
            print("❌ JWT secret not found")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = deploy_clock_fix()
    if success:
        print("\n🎉 Clock skew fix deployed successfully!")
        print("✅ Authentication should now work correctly")
    else:
        print("\n❌ Deployment failed")
        print("🔧 Try running: python deploy-supabase-auth.py")
    
    sys.exit(0 if success else 1)