#!/usr/bin/env python3
"""
Test script to verify environment variables are loaded correctly
"""

import os
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("📄 Loading .env file...")
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value
    
    print("✅ .env file loaded")
    return True

def check_vars():
    """Check environment variables"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'SUPABASE_JWT_SECRET',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_STORAGE_BUCKET'
    ]
    
    print("\n🔍 Checking environment variables:\n")
    
    all_present = True
    
    for var in required_vars:
        value = os.environ.get(var, '')
        
        if value:
            # Show first 20 chars for security
            display_value = value[:20] + '...' if len(value) > 20 else value
            print(f"✅ {var:30} = {display_value}")
        else:
            print(f"❌ {var:30} = NOT SET")
            all_present = False
    
    print()
    
    if all_present:
        print("✅ All required environment variables are set!")
        return True
    else:
        print("❌ Some environment variables are missing!")
        return False

if __name__ == '__main__':
    print("🧪 CivicFix Environment Variable Test")
    print("=" * 60)
    print()
    
    load_env_file()
    success = check_vars()
    
    print("=" * 60)
    
    if success:
        print("✅ Environment configuration is valid!")
        exit(0)
    else:
        print("❌ Environment configuration has issues!")
        exit(1)
