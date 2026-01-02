#!/usr/bin/env python3
"""
Test script to check issue media data
"""

import requests
import json

# Configuration
BASE_URL = "https://civicfix-server.asolvitra.tech"  # Production backend URL
API_BASE = f"{BASE_URL}/api/v1"

def test_issue_media():
    """Test issue media data"""
    print("📸 Testing Issue Media Data")
    print("=" * 50)
    
    # Get all issues first
    print("\n1. Getting all issues...")
    response = requests.get(f"{API_BASE}/issues?per_page=5")
    if response.status_code == 200:
        data = response.json()
        issues = data['issues']
        print(f"✅ Found {len(issues)} issues")
        
        for i, issue in enumerate(issues[:3]):
            print(f"\n--- Issue {i+1}: {issue['title']} ---")
            print(f"ID: {issue['id']}")
            print(f"Image URLs: {issue.get('image_urls', 'Not found')}")
            print(f"Image URLs type: {type(issue.get('image_urls'))}")
            print(f"Image URLs length: {len(issue.get('image_urls', []))}")
            
            # Get detailed issue data
            print(f"\n2. Getting detailed data for issue {issue['id']}...")
            detail_response = requests.get(f"{API_BASE}/issues/{issue['id']}")
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                issue_detail = detail_data['issue']
                print(f"✅ Detailed issue data:")
                print(f"   Title: {issue_detail['title']}")
                print(f"   Image URLs: {issue_detail.get('image_urls', 'Not found')}")
                print(f"   Image URLs type: {type(issue_detail.get('image_urls'))}")
                print(f"   Image URLs length: {len(issue_detail.get('image_urls', []))}")
                
                # Print full JSON for debugging
                print(f"\n   Full JSON:")
                print(json.dumps(issue_detail, indent=2))
            else:
                print(f"❌ Failed to get detailed issue: {detail_response.status_code}")
            
            print("-" * 50)
    else:
        print(f"❌ Failed to get issues: {response.status_code}")

if __name__ == "__main__":
    try:
        test_issue_media()
        print("\n🎉 Media test completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")