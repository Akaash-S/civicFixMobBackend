"""
Test script to debug authentication flow
"""
import requests
import json
import base64

BASE_URL = "https://civicfixmobbackend.onrender.com"

def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing health endpoint...")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_check_user_invalid_token():
    """Test check-user with invalid token"""
    print("=" * 60)
    print("Testing check-user with invalid token...")
    print("=" * 60)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/check-user",
        json={"id_token": "invalid_token"}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_check_user_missing_token():
    """Test check-user with missing token"""
    print("=" * 60)
    print("Testing check-user with missing token...")
    print("=" * 60)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/check-user",
        json={}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_create_user_invalid_token():
    """Test create-user with invalid token"""
    print("=" * 60)
    print("Testing create-user with invalid token...")
    print("=" * 60)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/create-user",
        json={
            "id_token": "invalid_token",
            "password": "testpassword123",
            "language": "en"
        }
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_create_user_missing_password():
    """Test create-user with missing password"""
    print("=" * 60)
    print("Testing create-user with missing password...")
    print("=" * 60)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/create-user",
        json={
            "id_token": "test_token",
            "language": "en"
        }
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_create_user_short_password():
    """Test create-user with short password"""
    print("=" * 60)
    print("Testing create-user with short password...")
    print("=" * 60)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/create-user",
        json={
            "id_token": "test_token",
            "password": "short",
            "language": "en"
        }
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_login_nonexistent_user():
    """Test login with non-existent user"""
    print("=" * 60)
    print("Testing login with non-existent user...")
    print("=" * 60)
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
    print("=" * 60)
    print("Testing login with missing email...")
    print("=" * 60)
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
    
    print("=" * 60)
    print("Testing login with missing password...")
    print("=" * 60)
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

def test_database_connection():
    """Test if database is accessible"""
    print("=" * 60)
    print("Testing database connection via stats endpoint...")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CIVICFIX BACKEND AUTHENTICATION TEST SUITE")
    print("=" * 60 + "\n")
    
    test_health()
    test_database_connection()
    test_check_user_missing_token()
    test_check_user_invalid_token()
    test_create_user_missing_password()
    test_create_user_short_password()
    test_create_user_invalid_token()
    test_login_missing_fields()
    test_login_nonexistent_user()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60 + "\n")

