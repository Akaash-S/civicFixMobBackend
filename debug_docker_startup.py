#!/usr/bin/env python3
"""
Debug Docker Startup Issues
Help identify why the backend container is failing to start
"""

import subprocess
import sys

def run_command(command, description):
    """Run a command and return output"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def debug_docker_startup():
    """Debug Docker startup issues"""
    
    server_ip = "3.110.42.224"
    server_user = "ubuntu"
    project_dir = "/home/ubuntu/civicFix"
    
    print("🐳 Docker Startup Debug")
    print("=" * 40)
    
    commands = [
        # Check server connectivity
        (f"ping -c 1 {server_ip}", "Test server connectivity"),
        
        # Check Docker status on server
        (f"ssh {server_user}@{server_ip} 'docker --version'", "Check Docker version"),
        (f"ssh {server_user}@{server_ip} 'docker-compose --version'", "Check Docker Compose version"),
        
        # Check project directory
        (f"ssh {server_user}@{server_ip} 'ls -la {project_dir}/backend/'", "List backend directory"),
        
        # Check environment file
        (f"ssh {server_user}@{server_ip} 'cd {project_dir}/backend && ls -la .env'", "Check .env file exists"),
        (f"ssh {server_user}@{server_ip} 'cd {project_dir}/backend && wc -l .env'", "Check .env file size"),
        
        # Check Docker Compose file
        (f"ssh {server_user}@{server_ip} 'cd {project_dir}/backend && ls -la docker-compose.yml'", "Check docker-compose.yml"),
        
        # Check current container status
        (f"ssh {server_user}@{server_ip} 'cd {project_dir}/backend && docker-compose ps'", "Check container status"),
        
        # Check Docker logs
        (f"ssh {server_user}@{server_ip} 'cd {project_dir}/backend && docker-compose logs --tail=50'", "Check container logs"),
        
        # Check if containers are running
        (f"ssh {server_user}@{server_ip} 'docker ps -a'", "Check all containers"),
        
        # Check system resources
        (f"ssh {server_user}@{server_ip} 'df -h'", "Check disk space"),
        (f"ssh {server_user}@{server_ip} 'free -h'", "Check memory usage"),
        
        # Try to validate docker-compose file
        (f"ssh {server_user}@{server_ip} 'cd {project_dir}/backend && docker-compose config'", "Validate docker-compose.yml"),
    ]
    
    print("Running diagnostic commands...\n")
    
    for command, description in commands:
        print(f"\n{'='*60}")
        success = run_command(command, description)
        if not success and "ping" not in command:
            print("⚠️  This command failed - may indicate an issue")
    
    print(f"\n{'='*60}")
    print("🔧 TROUBLESHOOTING SUGGESTIONS")
    print("=" * 60)
    
    print("\n1. Check the container logs above for specific error messages")
    print("2. Common issues and solutions:")
    print("   - Missing environment variables → Check .env file")
    print("   - Port conflicts → Check if port 5000 is in use")
    print("   - Syntax errors in code → Check app.py syntax")
    print("   - Missing dependencies → Check requirements.txt")
    print("   - Docker Compose syntax → Validate YAML format")
    print("   - Insufficient resources → Check disk space and memory")
    
    print("\n3. Manual debugging steps:")
    print(f"   ssh {server_user}@{server_ip}")
    print(f"   cd {project_dir}/backend")
    print("   docker-compose down")
    print("   docker-compose up --build")
    print("   # Watch the build process for errors")
    
    print("\n4. If the issue persists:")
    print("   - Check the Dockerfile for syntax errors")
    print("   - Verify all required files are present")
    print("   - Test the app.py file locally first")
    print("   - Check server system logs: journalctl -u docker")

if __name__ == "__main__":
    debug_docker_startup()