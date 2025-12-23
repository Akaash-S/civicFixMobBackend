#!/usr/bin/env python3
"""
CivicFix Backend - Docker Deployment Test Script
Tests the Docker containerized version of the backend
"""

import requests
import time
import subprocess
import sys
import json

def run_command(cmd, shell=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_docker_deployment():
    """Test Docker deployment"""
    print("🐳 Testing CivicFix Backend Docker Deployment")
    print("=" * 50)
    
    # Stop any existing containers
    print("🛑 Stopping existing containers...")
    run_command("docker-compose -f docker-compose-clean.yml down")
    
    # Build and start containers
    print("🔨 Building and starting containers...")
    success, stdout, stderr = run_command("docker-compose -f docker-compose-clean.yml up -d --build")
    
    if not success:
        print(f"❌ Failed to start containers: {stderr}")
        return False
    
    print("✅ Containers started successfully")
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(30)
    
    # Check container status
    print("📊 Container Status:")
    success, stdout, stderr = run_command("docker-compose -f docker-compose-clean.yml ps")
    print(stdout)
    
    # Test health endpoint
    print("🏥 Testing health endpoint...")
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health check passed!")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
                break
        except Exception as e:
            print(f"⏳ Attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(10)
            else:
                print("❌ Health check failed after all retries")
                return False
    
    # Test API endpoints
    print("🔍 Testing API endpoints...")
    
    # Test categories
    try:
        response = requests.get("http://localhost/api/v1/categories", timeout=10)
        if response.status_code == 200:
            print("✅ Categories endpoint working")
        else:
            print(f"❌ Categories endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Categories endpoint error: {e}")
    
    # Test issues
    try:
        response = requests.get("http://localhost/api/v1/issues", timeout=10)
        if response.status_code == 200:
            print("✅ Issues endpoint working")
        else:
            print(f"❌ Issues endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Issues endpoint error: {e}")
    
    # Show logs
    print("📋 Recent logs:")
    success, stdout, stderr = run_command("docker-compose -f docker-compose-clean.yml logs --tail=10")
    print(stdout)
    
    print("\n🎉 Docker deployment test completed!")
    print("🔧 To stop containers: docker-compose -f docker-compose-clean.yml down")
    
    return True

if __name__ == "__main__":
    success = test_docker_deployment()
    sys.exit(0 if success else 1)