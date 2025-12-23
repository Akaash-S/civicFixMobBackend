#!/usr/bin/env python3
"""
CivicFix Backend - Docker Deployment Test Script
Tests the AWS-integrated Docker containerized version of the backend
"""

import requests
import time
import subprocess
import sys
import json
import os

def run_command(cmd, shell=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_env_file():
    """Check if .env file exists with required AWS variables"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Please copy .env-clean to .env and configure with your AWS credentials")
        return False
    
    required_vars = [
        'SECRET_KEY', 'DATABASE_URL', 'AWS_ACCESS_KEY_ID', 
        'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET_NAME', 'AWS_REGION'
    ]
    
    missing_vars = []
    with open('.env', 'r') as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content or f"{var}=your-" in env_content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or unconfigured environment variables: {', '.join(missing_vars)}")
        print("Please update .env file with your actual AWS credentials")
        return False
    
    print("✅ Environment file configured")
    return True

def test_docker_deployment():
    """Test Docker deployment"""
    print("🐳 Testing CivicFix Backend AWS-Integrated Docker Deployment")
    print("=" * 60)
    
    # Check environment configuration
    if not check_env_file():
        return False
    
    # Stop any existing containers
    print("🛑 Stopping existing containers...")
    run_command("docker-compose down")
    
    # Build and start containers
    print("🔨 Building and starting containers...")
    success, stdout, stderr = run_command("docker-compose up -d --build")
    
    if not success:
        print(f"❌ Failed to start containers: {stderr}")
        return False
    
    print("✅ Containers started successfully")
    
    # Wait for services to be ready (longer wait for AWS services)
    print("⏳ Waiting for AWS services to be ready...")
    time.sleep(60)
    
    # Check container status
    print("📊 Container Status:")
    success, stdout, stderr = run_command("docker-compose ps")
    print(stdout)
    
    # Test health endpoint
    print("🏥 Testing health endpoint...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost/health", timeout=15)
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Health check passed!")
                print(f"Response: {json.dumps(health_data, indent=2)}")
                
                # Check AWS services status
                services = health_data.get('services', {})
                if services.get('database') == 'healthy' and services.get('s3') == 'healthy':
                    print("✅ AWS RDS and S3 are healthy!")
                else:
                    print("⚠️ Some AWS services may not be properly configured")
                    print(f"Database: {services.get('database', 'unknown')}")
                    print(f"S3: {services.get('s3', 'unknown')}")
                break
        except Exception as e:
            print(f"⏳ Attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(15)
            else:
                print("❌ Health check failed after all retries")
                print("Checking container logs...")
                run_command("docker-compose logs --tail=20 backend")
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
    success, stdout, stderr = run_command("docker-compose logs --tail=15 backend")
    print(stdout)
    
    print("\n🎉 Docker deployment test completed!")
    print("🔧 Management commands:")
    print("  - View logs: docker-compose logs -f")
    print("  - Stop containers: docker-compose down")
    print("  - Restart: docker-compose restart")
    print("  - Rebuild: docker-compose up -d --build")
    
    return True

if __name__ == "__main__":
    success = test_docker_deployment()
    sys.exit(0 if success else 1)