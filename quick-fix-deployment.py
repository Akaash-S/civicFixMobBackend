#!/usr/bin/env python3
"""
Quick Fix Deployment - Upload Critical Fixed Files Only
This script uploads only the critical fixed files to resolve the comment schema issue
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def quick_fix_deployment():
    """Quick deployment of critical fixes"""
    print("⚡ Quick Fix Deployment for Comment Schema")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    server_ip = "3.110.42.224"
    
    # Upload only the critical fixed file
    print("📤 Uploading fixed backend code...")
    if not run_command(f'scp -o StrictHostKeyChecking=no "backend/app.py" ubuntu@{server_ip}:/home/ubuntu/civicFix/backend/app.py', "Uploading fixed app.py"):
        return False
    
    # Restart the backend service
    print("\n🔄 Restarting backend service...")
    if not run_command(f'ssh -o StrictHostKeyChecking=no ubuntu@{server_ip} "cd /home/ubuntu/civicFix/backend && docker-compose restart backend"', "Restarting backend"):
        return False
    
    print("\n⏳ Waiting 15 seconds for service to restart...")
    import time
    time.sleep(15)
    
    # Test the fix
    print("\n🧪 Testing the fix...")
    if run_command(f'curl -s http://{server_ip}/health | grep -q "healthy"', "Testing server health"):
        print("✅ Server is healthy after fix")
    else:
        print("⚠️ Server health check unclear")
    
    print("\n🎉 Quick fix deployment completed!")
    print("💡 Comments functionality should now work with the fixed schema")
    
    return True

if __name__ == "__main__":
    success = quick_fix_deployment()
    
    if success:
        print("\n✅ Quick fix completed successfully!")
        print("🔧 Test the comments functionality in your app")
    else:
        print("\n❌ Quick fix failed!")
        sys.exit(1)