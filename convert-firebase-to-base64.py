#!/usr/bin/env python3
"""
Firebase Service Account to Base64 Converter
Converts Firebase service account JSON to Base64 for environment variables
"""

import json
import base64
import sys
import os

def convert_firebase_to_base64(input_file, output_file=None):
    """Convert Firebase service account JSON to Base64"""
    
    try:
        # Read the service account JSON file
        with open(input_file, 'r') as f:
            service_account_data = json.load(f)
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in service_account_data]
        
        if missing_fields:
            print(f"❌ Error: Missing required fields: {missing_fields}")
            return False
        
        # Validate private key format
        private_key = service_account_data.get('private_key', '')
        if '-----BEGIN PRIVATE KEY-----' not in private_key:
            print("❌ Error: Invalid private key format - missing BEGIN marker")
            return False
        
        if '-----END PRIVATE KEY-----' not in private_key:
            print("❌ Error: Invalid private key format - missing END marker")
            return False
        
        if '\n' not in private_key:
            print("❌ Error: Invalid private key format - missing newlines")
            return False
        
        # Convert to JSON string (compact format)
        json_str = json.dumps(service_account_data, separators=(',', ':'))
        
        # Encode to Base64
        json_bytes = json_str.encode('utf-8')
        b64_encoded = base64.b64encode(json_bytes).decode('ascii')
        
        # Output results
        if output_file:
            with open(output_file, 'w') as f:
                f.write(b64_encoded)
            print(f"✅ Base64-encoded Firebase credentials saved to: {output_file}")
        else:
            print("✅ Base64-encoded Firebase credentials:")
            print(b64_encoded)
        
        print("\n📋 Environment Variable:")
        print(f"FIREBASE_SERVICE_ACCOUNT_B64={b64_encoded}")
        
        print("\n🔍 Validation:")
        print(f"   Project ID: {service_account_data.get('project_id')}")
        print(f"   Client Email: {service_account_data.get('client_email')}")
        print(f"   Private Key Length: {len(private_key)} characters")
        print(f"   Base64 Length: {len(b64_encoded)} characters")
        
        # Test decoding
        try:
            decoded_bytes = base64.b64decode(b64_encoded)
            decoded_json = json.loads(decoded_bytes.decode('utf-8'))
            print("   Decoding Test: ✅ Success")
        except Exception as e:
            print(f"   Decoding Test: ❌ Failed - {e}")
            return False
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {input_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {input_file}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🔧 Firebase Service Account to Base64 Converter")
        print("=" * 50)
        print()
        print("Usage:")
        print(f"  python {sys.argv[0]} <service-account.json> [output-file]")
        print()
        print("Examples:")
        print(f"  python {sys.argv[0]} service-account.json")
        print(f"  python {sys.argv[0]} service-account.json firebase.b64")
        print()
        print("This tool converts Firebase service account JSON to Base64")
        print("to prevent OpenSSL deserialization errors in production.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("🔧 Firebase Service Account to Base64 Converter")
    print("=" * 50)
    print(f"Input file: {input_file}")
    if output_file:
        print(f"Output file: {output_file}")
    print()
    
    success = convert_firebase_to_base64(input_file, output_file)
    
    if success:
        print("\n🎉 Conversion completed successfully!")
        print("\n📝 Next steps:")
        print("1. Copy the FIREBASE_SERVICE_ACCOUNT_B64 value")
        print("2. Set it as an environment variable in your deployment platform")
        print("3. Remove the original service-account.json file for security")
        print("4. Test your Firebase authentication")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()