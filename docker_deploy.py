#!/usr/bin/env python3
"""
CivicFix Docker Deployment Script
Simple script to build and deploy the Docker container
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description, timeout=120):
    """Run a command with timeout and proper error handling"""
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
        
        # Print output in real-time style
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

def check_prerequisites():
    """Check if Docker is available"""
    print("🔍 Checking Prerequisites")
    print("=" * 50)
    
    if not run_command("docker --version", "Check Docker", 10):
        print("❌ Docker is not available. Please install Docker Desktop.")
        return False
    
    if not run_command("docker-compose --version", "Check Docker Compose", 10):
        print("❌ Docker Compose is not available.")
        return False
    
    return True

def cleanup_containers():
    """Stop and remove existing containers"""
    print("\n🧹 Cleaning up existing containers")
    print("=" * 50)
    
    # Stop containers
    run_command("docker-compose down", "Stop existing containers", 30)
    
    # Remove dangling images
    run_command("docker image prune -f", "Remove dangling images", 30)
    
    return True

def build_container():
    """Build the Docker container"""
    print("\n🏗️ Building Docker Container")
    print("=" * 50)
    
    # Build with no cache for clean build
    if not run_command("docker-compose build --no-cache backend", "Build backend container", 300):
        return False
    
    return True

def start_container():
    """Start the container and test it"""
    print("\n🚀 Starting Container")
    print("=" * 50)
    
    # Start in detached mode
    if not run_command("docker-compose up -d backend", "Start backend container", 60):
        return False
    
    # Wait for startup
    print("⏳ Waiting for container to start...")
    time.sleep(15)
    
    # Check container status
    run_command("docker-compose ps", "Check container status", 10)
    
    # Get logs
    run_command("docker-compose logs --tail=20 backend", "Get container logs", 10)
    
    return True

def test_container():
    """Test if the container is working"""
    print("\n🧪 Testing Container")
    print("=" * 50)
    
    # Test health endpoint
    print("Testing health endpoint...")
    for i in range(5):
        if run_command("curl -f http://localhost:5000/health", f"Test health endpoint (attempt {i+1})", 10):
            return True
        print(f"⏳ Waiting 10 seconds before retry...")
        time.sleep(10)
    
    print("❌ Health endpoint test failed after 5 attempts")
    
    # Get detailed logs for debugging
    run_command("docker-compose logs backend", "Get full container logs", 30)
    
    return False

def deploy_with_nginx():
    """Deploy with nginx proxy"""
    print("\n🌐 Deploying with Nginx")
    print("=" * 50)
    
    if not run_command("docker-compose up -d", "Start all services", 60):
        return False
    
    # Wait for nginx
    time.sleep(10)
    
    # Test nginx proxy
    if run_command("curl -f http://localhost/health", "Test nginx proxy", 10):
        print("✅ Nginx proxy is working!")
        return True
    else:
        print("⚠️ Nginx proxy test failed, but backend might still be working")
        return True

def main():
    """Main deployment function"""
    print("🐳 CivicFix Docker Deployment")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Check prerequisites
        if not check_prerequisites():
            return False
        
        # Cleanup
        cleanup_containers()
        
        # Build
        if not build_container():
            print("❌ Container build failed")
            return False
        
        # Start
        if not start_container():
            print("❌ Container start failed")
            return False
        
        # Test
        if not test_container():
            print("❌ Container test failed")
            return False
        
        # Deploy with nginx (optional)
        deploy_with_nginx()
        
        print("\n🎉 Docker Deployment Successful!")
        print("=" * 50)
        print("✅ Backend container is running")
        print("✅ Health endpoint is accessible")
        print("✅ API is ready for use")
        print("\nUseful commands:")
        print("  docker-compose ps                    # Check status")
        print("  docker-compose logs backend          # View logs")
        print("  curl http://localhost:5000/health    # Test health")
        print("  docker-compose down                  # Stop services")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)