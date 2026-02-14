"""
Test script to verify database initialization endpoint
"""
import requests
import json

BASE_URL = "https://civicfixmobbackend.onrender.com"

def test_init_db():
    """Test manual database initialization"""
    print("=" * 60)
    print("Testing manual database initialization...")
    print("=" * 60)
    response = requests.post(f"{BASE_URL}/init-db")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Database initialized successfully!")
            print(f"Tables created: {result.get('new_tables', [])}")
        else:
            print("\n❌ Database initialization failed!")
    except:
        print(f"Response: {response.text}")
    print()

def test_stats_after_init():
    """Test stats endpoint after initialization"""
    print("=" * 60)
    print("Testing stats endpoint after initialization...")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print(f"Status: {response.status_code}")
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Stats endpoint working!")
        else:
            print("\n❌ Stats endpoint still failing!")
    except:
        print(f"Response: {response.text}")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION TEST")
    print("=" * 60 + "\n")
    
    test_init_db()
    test_stats_after_init()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60 + "\n")
    print("Next steps:")
    print("1. If initialization succeeded, test authentication from frontend")
    print("2. If initialization failed, check Render logs for errors")
    print("3. Verify all environment variables are set correctly on Render")
