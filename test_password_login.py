"""
Test script to debug password login endpoint
"""
import requests
import json

BASE_URL = "https://civicfixmobbackend.onrender.com"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_login_nonexistent_user():
    """Test login with non-existent user"""
    print("Testing login with non-existent user...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login-with-password",
        json={"email": "nonexistent@example.com", "password": "testpassword"}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_login_missing_fields():
    """Test login with missing fields"""
    print("Testing login with missing email...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login-with-password",
        json={"password": "testpassword"}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()
    
    print("Testing login with missing password...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login-with-password",
        json={"email": "test@example.com"}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

if __name__ == "__main__":
    test_health()
    test_login_nonexistent_user()
    test_login_missing_fields()
