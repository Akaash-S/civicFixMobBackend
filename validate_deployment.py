#!/usr/bin/env python3
"""
CivicFix Backend - Deployment Validation Script
Validates that the deployed system matches the perfect local system
"""

import os
import sys
import requests
import time
from datetime import datetime

def validate_deployment():
    """Validate the deployed authentication system"""
    
    production_url = "http://3.110.42.224:80"
    
    print("🚀 CivicFix Deployment Validation")
    print("=" * 50)
    print(f"🌐 Production URL: {production_url}")
    print(f"⏰ Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. 🏥 Health Check Validation...")
    try:
        response = requests.get(f"{production_url}/health", timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            version = health.get('version', 'unknown')
            auth_type = health.get('authentication', 'unknown')
            supabase_status = health.get('services', {}).get('supabase_auth', 'unknown')
            
            print(f"   ✅ Server responding: HTTP {response.status_code}")
            print(f"   ✅ Version: {version}")
            print(f"   ✅ Authentication: {auth_type}")
            print(f"   ✅ Supabase Status: {supabase_status}")
            
            if auth_type == 'supabase' and supabase_status == 'healthy':
                print("   ✅ Health check passed!")
                health_passed = True
            else:
                print("   ❌ Health check failed - wrong auth type or unhealthy status")
                health_passed = False
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            health_passed = False
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        health_passed = False
    
    # Test 2: Authentication System Validation
    print("\n2. 🔐 Authentication System Validation...")
    
    if health_passed:
        # Run the comprehensive authentication test
        print("   🧪 Running comprehensive authentication test...")
        
        try:
            # Import and run the test suite
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from test_auth_quick import AuthTestSuite
            
            test_suite = AuthTestSuite()
            success = test_suite.run_all_tests()
            
            if success:
                print("   ✅ Authentication system validation passed!")
                auth_passed = True
            else:
                print("   ❌ Authentication system validation failed!")
                auth_passed = False
                
        except Exception as e:
            print(f"   ❌ Authentication test error: {e}")
            auth_passed = False
    else:
        print("   ⚠️ Skipping authentication test due to health check failure")
        auth_passed = False
    
    # Test 3: Docker Container Status
    print("\n3. 🐳 Docker Container Validation...")
    print("   ℹ️ To check container status manually:")
    print("   ssh ubuntu@3.110.42.224 'docker-compose ps'")
    print("   ssh ubuntu@3.110.42.224 'docker-compose logs --tail=50'")
    
    # Test 4: Environment Configuration
    print("\n4. ⚙️ Environment Configuration Validation...")
    print("   ℹ️ To check environment variables manually:")
    print("   ssh ubuntu@3.110.42.224 'cd /home/ubuntu/civicFix/backend && grep SUPABASE_JWT_SECRET .env'")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT VALIDATION SUMMARY")
    print("=" * 50)
    
    if health_passed and auth_passed:
        print("🎉 DEPLOYMENT VALIDATION SUCCESSFUL!")
        print("✅ Health check passed")
        print("✅ Authentication system working perfectly")
        print("✅ Production system matches local system")
        print("\n🎯 Your deployment is ready for production use!")
        return True
    else:
        print("❌ DEPLOYMENT VALIDATION FAILED!")
        if not health_passed:
            print("❌ Health check failed")
        if not auth_passed:
            print("❌ Authentication system failed")
        
        print("\n🔧 Troubleshooting Steps:")
        print("1. Check if containers are running:")
        print("   ssh ubuntu@3.110.42.224 'docker-compose ps'")
        print("2. Check container logs:")
        print("   ssh ubuntu@3.110.42.224 'docker-compose logs --tail=100'")
        print("3. Restart containers:")
        print("   ssh ubuntu@3.110.42.224 'docker-compose restart'")
        print("4. Rebuild and redeploy:")
        print("   ssh ubuntu@3.110.42.224 'docker-compose up -d --build'")
        
        return False

def main():
    """Main validation function"""
    success = validate_deployment()
    
    if success:
        print("\n🎉 Deployment validation completed successfully!")
        print("Your perfect authentication system is now deployed and working!")
    else:
        print("\n⚠️ Deployment validation failed!")
        print("Please fix the issues above and try again.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())