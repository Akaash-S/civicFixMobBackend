#!/usr/bin/env python3
"""
Test requirements.txt for dependency conflicts
"""

import subprocess
import sys
import tempfile
import os

def test_requirements():
    """Test if requirements.txt can be installed without conflicts"""
    print("🧪 Testing requirements.txt for dependency conflicts...")
    
    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = os.path.join(temp_dir, "test_venv")
        
        try:
            # Create virtual environment
            print("📦 Creating temporary virtual environment...")
            result = subprocess.run([
                sys.executable, "-m", "venv", venv_path
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"❌ Failed to create virtual environment: {result.stderr}")
                return False
            
            # Get pip path
            if os.name == 'nt':  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
                python_path = os.path.join(venv_path, "Scripts", "python.exe")
            else:  # Unix/Linux
                pip_path = os.path.join(venv_path, "bin", "pip")
                python_path = os.path.join(venv_path, "bin", "python")
            
            # Upgrade pip
            print("⬆️ Upgrading pip...")
            result = subprocess.run([
                python_path, "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"⚠️ Pip upgrade warning: {result.stderr}")
            
            # Test install requirements
            print("📋 Testing requirements installation...")
            result = subprocess.run([
                pip_path, "install", "--dry-run", "-r", "requirements-clean.txt"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Requirements test passed - no conflicts detected!")
                print("📋 Dependency resolution successful")
                return True
            else:
                print(f"❌ Requirements test failed:")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Requirements test timed out")
            return False
        except Exception as e:
            print(f"❌ Requirements test error: {e}")
            return False

def suggest_fixes():
    """Suggest fixes for common dependency issues"""
    print("\n🔧 Suggested fixes for dependency conflicts:")
    print("1. Remove version pins and let pip resolve automatically")
    print("2. Use compatible version ranges instead of exact versions")
    print("3. Check for duplicate packages with different names")
    print("4. Update to latest compatible versions")

if __name__ == "__main__":
    print("🔍 CivicFix Requirements Dependency Test")
    print("=" * 50)
    
    if not os.path.exists("requirements-clean.txt"):
        print("❌ requirements-clean.txt not found")
        sys.exit(1)
    
    success = test_requirements()
    
    if not success:
        suggest_fixes()
        sys.exit(1)
    else:
        print("\n🎉 All dependency tests passed!")
        print("✅ Ready for Docker build")
        sys.exit(0)