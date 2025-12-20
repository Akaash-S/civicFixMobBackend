#!/usr/bin/env python3
"""
Python Path Fix Script for CivicFix Backend
Fixes common Python path issues on different systems
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def detect_python_executable():
    """Detect the correct Python executable"""
    python_executables = [
        'python3',
        'python',
        'py',
        sys.executable
    ]
    
    for executable in python_executables:
        try:
            result = subprocess.run([executable, '--version'], 
                                  capture_output=True, text=True, check=True)
            if 'Python 3.' in result.stdout:
                print(f"✅ Found Python: {executable}")
                print(f"   Version: {result.stdout.strip()}")
                return executable
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    return None

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    in_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        print("✅ Virtual environment detected")
        print(f"   Python path: {sys.executable}")
        return True
    else:
        print("⚠️  Not in a virtual environment")
        return False

def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return True
    
    python_exe = detect_python_executable()
    if not python_exe:
        print("❌ No suitable Python executable found")
        return False
    
    try:
        print("🔄 Creating virtual environment...")
        subprocess.run([python_exe, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_activation_command():
    """Get the correct activation command for the platform"""
    system = platform.system().lower()
    
    if system == 'windows':
        return 'venv\\Scripts\\activate'
    else:
        return 'source venv/bin/activate'

def install_dependencies():
    """Install dependencies in virtual environment"""
    system = platform.system().lower()
    
    if system == 'windows':
        pip_exe = 'venv\\Scripts\\pip'
        python_exe = 'venv\\Scripts\\python'
    else:
        pip_exe = 'venv/bin/pip'
        python_exe = 'venv/bin/python'
    
    try:
        print("🔄 Installing dependencies...")
        subprocess.run([pip_exe, 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([pip_exe, 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_run_scripts():
    """Create platform-specific run scripts"""
    system = platform.system().lower()
    
    if system == 'windows':
        # Create Windows batch file
        batch_content = '''@echo off
echo Starting CivicFix Backend...
call venv\\Scripts\\activate
python run.py
pause
'''
        with open('start_backend.bat', 'w') as f:
            f.write(batch_content)
        
        print("✅ Created start_backend.bat for Windows")
    
    else:
        # Create Unix shell script
        shell_content = '''#!/bin/bash
echo "Starting CivicFix Backend..."
source venv/bin/activate
python run.py
'''
        with open('start_backend.sh', 'w') as f:
            f.write(shell_content)
        
        # Make executable
        os.chmod('start_backend.sh', 0o755)
        print("✅ Created start_backend.sh for Unix/Linux")

def test_setup():
    """Test if the setup is working"""
    system = platform.system().lower()
    
    if system == 'windows':
        python_exe = 'venv\\Scripts\\python'
    else:
        python_exe = 'venv/bin/python'
    
    try:
        # Test Python executable
        result = subprocess.run([python_exe, '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Python test passed: {result.stdout.strip()}")
        
        # Test Flask import
        result = subprocess.run([python_exe, '-c', 'import flask; print("Flask version:", flask.__version__)'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Flask test passed: {result.stdout.strip()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup test failed: {e}")
        return False

def display_instructions():
    """Display final instructions"""
    system = platform.system().lower()
    activation_cmd = get_activation_command()
    
    print("\n🎉 Python environment setup completed!")
    print("\n📋 To run the CivicFix backend:")
    
    if system == 'windows':
        print("   Option 1: Double-click start_backend.bat")
        print("   Option 2: Run manually:")
        print(f"     {activation_cmd}")
        print("     python run.py")
    else:
        print("   Option 1: ./start_backend.sh")
        print("   Option 2: Run manually:")
        print(f"     {activation_cmd}")
        print("     python run.py")
    
    print("\n🔧 To activate virtual environment manually:")
    print(f"   {activation_cmd}")
    
    print("\n📚 Next steps:")
    print("1. Configure your .env file with AWS RDS credentials")
    print("2. Run database migrations: flask db upgrade")
    print("3. Start the backend server")

def main():
    """Main setup function"""
    print("🔧 CivicFix Python Environment Setup")
    print("=" * 40)
    
    # Check current Python
    python_exe = detect_python_executable()
    if not python_exe:
        print("❌ No Python 3.x found. Please install Python 3.8+")
        return False
    
    # Check if in virtual environment
    if not check_virtual_environment():
        # Create virtual environment
        if not create_virtual_environment():
            return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create run scripts
    create_run_scripts()
    
    # Test setup
    if not test_setup():
        return False
    
    # Display instructions
    display_instructions()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)