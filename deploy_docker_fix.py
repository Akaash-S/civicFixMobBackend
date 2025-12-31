#!/usr/bin/env python3
"""
Deploy Docker Fix - Diagnose and fix Docker deployment issues
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
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
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_docker_environment():
    """Check Docker environment"""
    print("🐳 Checking Docker Environment")
    print("=" * 40)
    
    # Check if Docker is running
    if not run_command("docker --version", "Check Docker version"):
        return False
    
    if not run_command("docker-compose --version", "Check Docker Compose version"):
        return False
    
    return True

def test_basic_startup():
    """Test basic Docker startup"""
    print("\n🧪 Testing Basic Docker Startup")
    print("=" * 40)
    
    # Test basic Python environment
    if not run_command("python test_docker_startup.py", "Test basic Python environment"):
        return False
    
    return True

def build_and_test_container():
    """Build and test the container"""
    print("\n🏗️ Building and Testing Container")
    print("=" * 40)
    
    # Stop any existing containers
    run_command("docker-compose down", "Stop existing containers")
    
    # Build the container
    if not run_command("docker-compose build --no-cache backend", "Build backend container"):
        return False
    
    # Test container startup with validation skipped
    print("\n🚀 Testing container startup...")
    
    # Start container in background
    if not run_command("docker-compose up -d backend", "Start backend container"):
        return False
    
    # Wait for startup
    print("⏳ Waiting for container to start...")
    time.sleep(10)
    
    # Check container status
    if not run_command("docker-compose ps", "Check container status"):
        return False
    
    # Check container logs
    run_command("docker-compose logs backend", "Check backend logs")
    
    # Test health endpoint
    if not run_command("curl -f http://localhost:5000/health", "Test health endpoint"):
        print("⚠️ Health endpoint test failed - checking container status...")
        run_command("docker-compose logs --tail=50 backend", "Get recent backend logs")
        return False
    
    print("✅ Container startup test passed!")
    return True

def cleanup():
    """Cleanup Docker resources"""
    print("\n🧹 Cleaning up...")
    run_command("docker-compose down", "Stop containers")

def main():
    """Main deployment fix function"""
    print("🔧 CivicFix Docker Deployment Fix")
    print("=" * 50)
    
    try:
        # Check Docker environment
        if not check_docker_environment():
            print("❌ Docker environment check failed")
            return False
        
        # Test basic startup
        if not test_basic_startup():
            print("❌ Basic startup test failed")
            return False
        
        # Build and test container
        if not build_and_test_container():
            print("❌ Container build/test failed")
            return False
        
        print("\n🎉 Docker deployment fix completed successfully!")
        print("✅ Backend container is running and healthy")
        print("✅ Health endpoint is accessible")
        print("\nYou can now run:")
        print("  docker-compose up -d")
        print("  curl http://localhost:5000/health")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Deployment fix interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Deployment fix failed: {e}")
        return False
    finally:
        cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)