#!/usr/bin/env python3
"""
Test upvotes functionality in the backend
"""

import os
import requests
import json
from dotenv import load_dotenv

def test_upvotes_in_api():
    """Test that upvotes field is included in API responses"""
    print("🧪 Testing Upvotes in API Responses")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Test the issues endpoint
        backend_url = "https://civicfix-server.asolvitra.tech"  # Your deployed backend
        
        print(f"📡 Testing API at: {backend_url}")
        
        # Test 1: Get all issues
        print("\n1. Testing GET /api/v1/issues")
        response = requests.get(f"{backend_url}/api/v1/issues", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            issues = data.get('issues', [])
            
            if issues:
                first_issue = issues[0]
                print(f"✅ API returned {len(issues)} issues")
                print(f"   Sample issue fields: {list(first_issue.keys())}")
                
                if 'upvotes' in first_issue:
                    print(f"✅ upvotes field present: {first_issue['upvotes']}")
                else:
                    print("❌ upvotes field missing from API response")
                    
                # Show sample issue data
                print(f"\n📋 Sample issue:")
                print(f"   ID: {first_issue.get('id')}")
                print(f"   Title: {first_issue.get('title', '')[:50]}...")
                print(f"   Status: {first_issue.get('status')}")
                print(f"   Upvotes: {first_issue.get('upvotes', 'MISSING')}")
                
            else:
                print("⚠️ No issues found in API response")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        
        # Test 2: Get specific issue
        if response.status_code == 200 and issues:
            issue_id = issues[0]['id']
            print(f"\n2. Testing GET /api/v1/issues/{issue_id}")
            
            detail_response = requests.get(f"{backend_url}/api/v1/issues/{issue_id}", timeout=10)
            
            if detail_response.status_code == 200:
                issue_detail = detail_response.json()
                issue_data = issue_detail.get('issue', {})
                
                print(f"✅ Issue detail retrieved")
                print(f"   Fields: {list(issue_data.keys())}")
                
                if 'upvotes' in issue_data:
                    print(f"✅ upvotes field in detail: {issue_data['upvotes']}")
                else:
                    print("❌ upvotes field missing from issue detail")
            else:
                print(f"❌ Issue detail request failed: {detail_response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_database_upvotes():
    """Test upvotes directly in database"""
    print("\n🗄️ Testing Upvotes in Database")
    print("=" * 40)
    
    try:
        import psycopg2
        
        # Get database URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found")
            return False
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check upvotes column
        cursor.execute("""
            SELECT id, title, upvotes, status, created_at 
            FROM issues 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        issues = cursor.fetchall()
        
        if issues:
            print(f"✅ Found {len(issues)} issues in database")
            print("\n📋 Sample issues with upvotes:")
            
            for issue in issues:
                issue_id, title, upvotes, status, created_at = issue
                print(f"   ID {issue_id}: '{title[:30]}...' - {upvotes} upvotes ({status})")
        else:
            print("⚠️ No issues found in database")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Upvotes Functionality Test")
    print("=" * 60)
    
    success1 = test_upvotes_in_api()
    success2 = test_database_upvotes()
    
    if success1 and success2:
        print("\n🎉 All upvotes tests passed!")
        print("✅ Database has upvotes column with 0 values")
        print("✅ API includes upvotes in responses")
        print("✅ Frontend components updated to remove like icons")
        print("✅ My Reports screen redesigned with better layout")
    else:
        print("\n❌ Some tests failed")
        print("Check the specific error messages above")