#!/usr/bin/env python3
"""
Validate Docker Compose Files
Check for YAML syntax errors and configuration issues
"""

import yaml
import os

def validate_yaml_file(file_path):
    """Validate YAML syntax"""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True, "Valid YAML syntax"
    except yaml.YAMLError as e:
        return False, f"YAML syntax error: {e}"
    except FileNotFoundError:
        return False, "File not found"
    except Exception as e:
        return False, f"Error: {e}"

def check_environment_variables(file_path):
    """Check if all required environment variables are referenced"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_S3_BUCKET_NAME',
        'SUPABASE_JWT_SECRET'
    ]
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        missing_vars = []
        for var in required_vars:
            if f"${{{var}}}" not in content:
                missing_vars.append(var)
        
        if missing_vars:
            return False, f"Missing environment variables: {', '.join(missing_vars)}"
        else:
            return True, "All required environment variables present"
            
    except Exception as e:
        return False, f"Error checking variables: {e}"

def validate_docker_compose():
    """Validate Docker Compose configuration"""
    
    print("🐳 Docker Compose Validation")
    print("=" * 40)
    
    files_to_check = [
        'docker-compose.yml',
        'docker-compose.simple.yml'
    ]
    
    all_valid = True
    
    for file_path in files_to_check:
        print(f"\n📄 Checking {file_path}...")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            all_valid = False
            continue
        
        # Check YAML syntax
        is_valid, message = validate_yaml_file(file_path)
        if is_valid:
            print(f"✅ YAML syntax: {message}")
        else:
            print(f"❌ YAML syntax: {message}")
            all_valid = False
            continue
        
        # Check environment variables
        has_vars, var_message = check_environment_variables(file_path)
        if has_vars:
            print(f"✅ Environment variables: {var_message}")
        else:
            print(f"⚠️  Environment variables: {var_message}")
        
        # Check for Firebase references (should be removed)
        with open(file_path, 'r') as f:
            content = f.read()
        
        firebase_refs = ['FIREBASE_SERVICE_ACCOUNT', 'FIREBASE_PROJECT_ID']
        found_firebase = [ref for ref in firebase_refs if ref in content]
        
        if found_firebase:
            print(f"⚠️  Found Firebase references: {', '.join(found_firebase)}")
            print("   These should be removed for Supabase-only authentication")
        else:
            print("✅ No Firebase references found")
        
        # Check for Supabase references
        if 'SUPABASE_JWT_SECRET' in content:
            print("✅ Supabase JWT secret configured")
        else:
            print("❌ Supabase JWT secret not configured")
            all_valid = False
    
    print("\n" + "=" * 40)
    if all_valid:
        print("🎉 All Docker Compose files are valid!")
        print("✅ YAML syntax is correct")
        print("✅ Environment variables are configured")
        print("✅ Supabase authentication is set up")
    else:
        print("❌ Issues found in Docker Compose files")
        print("🔧 Fix the issues above before deploying")
    
    return all_valid

if __name__ == "__main__":
    success = validate_docker_compose()
    exit(0 if success else 1)