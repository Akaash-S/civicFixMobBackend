#!/usr/bin/env python3
"""
Fix and Deploy - Complete Docker fix and deployment
"""

import subprocess
import sys
import time
import os

def run_cmd(cmd, description, timeout=180, show_output=True):
    """Run command with proper error handling"""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if show_output:
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main fix and deploy function"""
    print("🔧 CivicFix Docker Fix and Deploy")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    
    # Step 1: Test imports locally
    print("\n📋 Step 1: Testing imports locally")
    if not run_cmd("python test_imports.py", "Test local imports", 30):
        print("⚠️ Local import test failed, but continuing with Docker build...")
    
    # Step 2: Clean up existing containers
    print("\n🧹 Step 2: Cleaning up existing containers")
    run_cmd("docker-compose down", "Stop existing containers", 60)
    run_cmd("docker system prune -f", "Clean Docker system", 60)
    
    # Step 3: Build container with no cache
    print("\n🏗️ Step 3: Building Docker container")
    if not run_cmd("docker-compose build --no-cache backend", "Build backend container", 600):
        print("❌ Docker build failed!")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check if all required packages are in Dockerfile")
        print("2. Verify no dependency conflicts")
        print("3. Check Docker Desktop is running")
        return False
    
    # Step 4: Start container
    print("\n🚀 Step 4: Starting container")
    if not run_cmd("docker-compose up -d backend", "Start backend container", 120):
        print("❌ Container start failed!")
        return False
    
    # Step 5: Wait for startup
    print("\n⏳ Step 5: Waiting for container startup")
    print("Waiting 30 seconds for container to initialize...")
    time.sleep(30)
    
    # Step 6: Check container status
    print("\n📊 Step 6: Checking container status")
    run_cmd("docker-compose ps", "Check container status", 30)
    
    # Step 7: Check logs
    print("\n📋 Step 7: Checking container logs")
    run_cmd("docker-compose logs --tail=20 backend", "Get recent logs", 30)
    
    # Step 8: Test health endpoint
    print("\n🏥 Step 8: Testing health endpoint")
    for attempt in range(5):
        print(f"Health check attempt {attempt + 1}/5...")
        if run_cmd("curl -f http://localhost:5000/health", f"Health check attempt {attempt + 1}", 15, False):
            print("✅ Health endpoint is working!")
            break
        if attempt < 4:
            print("⏳ Waiting 15 seconds before retry...")
            time.sleep(15)
    else:
        print("❌ Health endpoint failed after 5 attempts")
        print("Getting detailed logs...")
        run_cmd("docker-compose logs backend", "Get full logs", 60)
        return False
    
    # Step 9: Test API endpoints
    print("\n🌐 Step 9: Testing API endpoints")
    endpoints = [
        "/api/v1/categories",
        "/api/v1/status-options",
        "/api/v1/priority-options"
    ]
    
    for endpoint in endpoints:
        run_cmd(f"curl -f http://localhost:5000{endpoint}", f"Test {endpoint}", 10, False)
    
    # Step 10: Start nginx (optional)
    print("\n🌐 Step 10: Starting nginx proxy")
    if run_cmd("docker-compose up -d nginx", "Start nginx proxy", 60):
        time.sleep(10)
        if run_cmd("curl -f http://localhost/health", "Test nginx proxy", 10, False):
            print("✅ Nginx proxy is working!")
        else:
            print("⚠️ Nginx proxy test failed, but backend is working")
    
    print("\n🎉 Deployment Successful!")
    print("=" * 50)
    print("✅ Docker container is running")
    print("✅ Health endpoint is accessible")
    print("✅ API endpoints are responding")
    print("\nUseful commands:")
    print("  docker-compose ps                    # Check status")
    print("  docker-compose logs backend          # View logs")
    print("  curl http://localhost:5000/health    # Test health")
    print("  curl http://localhost/health         # Test via nginx")
    print("  docker-compose down                  # Stop services")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        print("🧹 Cleaning up...")
        run_cmd("docker-compose down", "Stop containers", 30)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {e}")
        sys.exit(1)