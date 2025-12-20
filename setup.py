#!/usr/bin/env python3
"""
CivicFix Backend Setup Script
Automated setup for development environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    requirements = {
        'python': 'python --version',
        'pip': 'pip --version',
        'git': 'git --version'
    }
    
    missing = []
    for tool, command in requirements.items():
        if not run_command(command, f"Checking {tool}"):
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing required tools: {', '.join(missing)}")
        print("Please install the missing tools and run setup again.")
        sys.exit(1)
    
    print("✅ All requirements satisfied")

def setup_virtual_environment():
    """Create and activate virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return
    
    if not run_command("python -m venv venv", "Creating virtual environment"):
        sys.exit(1)
    
    # Activation command varies by OS
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    print(f"💡 To activate virtual environment, run: {activate_cmd}")
    return pip_cmd

def install_dependencies(pip_cmd=None):
    """Install Python dependencies"""
    if pip_cmd is None:
        pip_cmd = "pip"
    
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True

def setup_environment_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your configuration")
    else:
        print("❌ .env.example not found")

def setup_directories():
    """Create necessary directories"""
    directories = ['logs', 'uploads', 'migrations']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def display_next_steps():
    """Display next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration:")
    print("   - Database URL (PostgreSQL)")
    print("   - AWS credentials and S3 bucket")
    print("   - Firebase service account file")
    print("   - Redis URL")
    print("\n2. Place your Firebase service account JSON file in the backend directory")
    print("\n3. Initialize the database:")
    print("   flask db init")
    print("   flask db migrate -m 'Initial migration'")
    print("   flask db upgrade")
    print("\n4. Run the application:")
    print("   python run.py")
    print("\n5. Test the health endpoint:")
    print("   curl http://localhost:5000/health")
    print("\n📚 For detailed instructions, see README.md")

def main():
    """Main setup function"""
    print("🚀 CivicFix Backend Setup")
    print("=" * 40)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run setup steps
    check_requirements()
    pip_cmd = setup_virtual_environment()
    
    # Install dependencies
    if pip_cmd:
        install_dependencies(pip_cmd)
    else:
        install_dependencies()
    
    setup_environment_file()
    setup_directories()
    
    display_next_steps()

if __name__ == "__main__":
    main()