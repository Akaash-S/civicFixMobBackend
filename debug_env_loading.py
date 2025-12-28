#!/usr/bin/env python3
"""
Debug environment variable loading
Find where the JWT secret is coming from
"""

import os
from dotenv import load_dotenv

def check_env_sources():
    """Check different sources of environment variables"""
    
    print("🔍 Environment Variable Debug")
    print("=" * 50)
    
    # Check system environment (before loading .env)
    print("1. System Environment (before .env):")
    system_jwt = os.environ.get('SUPABASE_JWT_SECRET')
    if system_jwt:
        print(f"   ✅ Found in system: {system_jwt[:30]}...")
    else:
        print("   ❌ Not found in system environment")
    
    # Load .env file
    print("\n2. Loading .env file...")
    load_dotenv()
    
    # Check after loading .env
    print("3. After loading .env:")
    env_jwt = os.environ.get('SUPABASE_JWT_SECRET')
    if env_jwt:
        print(f"   ✅ Found after .env: {env_jwt[:30]}...")
    else:
        print("   ❌ Not found after loading .env")
    
    # Read .env file directly
    print("\n4. Reading .env file directly:")
    try:
        with open('.env', 'r') as f:
            content = f.read()
            
        for line in content.split('\n'):
            if 'SUPABASE_JWT_SECRET' in line and not line.startswith('#'):
                print(f"   📄 .env file contains: {line[:50]}...")
                
                # Extract the value
                if '=' in line:
                    key, value = line.split('=', 1)
                    print(f"   📄 .env value: {value[:30]}...")
                
    except Exception as e:
        print(f"   ❌ Error reading .env: {e}")
    
    # Check if there are multiple .env files being loaded
    print("\n5. Checking for other .env files:")
    possible_env_files = ['.env', '.env.local', '.env.development', '.env.production']
    
    for env_file in possible_env_files:
        if os.path.exists(env_file):
            print(f"   ✅ Found: {env_file}")
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    if 'SUPABASE_JWT_SECRET' in content:
                        for line in content.split('\n'):
                            if 'SUPABASE_JWT_SECRET' in line and not line.startswith('#'):
                                print(f"      🔑 {env_file}: {line[:50]}...")
            except Exception as e:
                print(f"      ❌ Error reading {env_file}: {e}")
        else:
            print(f"   ❌ Not found: {env_file}")

def main():
    check_env_sources()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("=" * 50)
    
    current_jwt = os.environ.get('SUPABASE_JWT_SECRET')
    if current_jwt:
        print(f"Current JWT Secret: {current_jwt}")
        print(f"Length: {len(current_jwt)} characters")
        
        if current_jwt.startswith('sb_secret_'):
            print("✅ This looks like a real Supabase JWT secret")
        else:
            print("⚠️ This doesn't look like a standard Supabase JWT secret")
    else:
        print("❌ No JWT secret found")

if __name__ == "__main__":
    main()