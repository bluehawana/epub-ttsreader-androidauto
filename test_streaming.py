#!/usr/bin/env python3
"""
Test script to verify audiobook streaming URLs work correctly
"""

import requests
import json
import sys

def test_streaming_url(url):
    """Test if a streaming URL works"""
    print(f"Testing URL: {url}")
    
    try:
        # Test HEAD request first
        head_response = requests.head(url, timeout=10)
        print(f"HEAD response: {head_response.status_code}")
        print(f"Content-Type: {head_response.headers.get('Content-Type')}")
        print(f"Content-Length: {head_response.headers.get('Content-Length')}")
        
        # Test partial GET request (first 1KB)
        headers = {'Range': 'bytes=0-1023'}
        get_response = requests.get(url, headers=headers, timeout=10)
        print(f"GET response: {get_response.status_code}")
        print(f"Content received: {len(get_response.content)} bytes")
        
        if get_response.status_code in [200, 206]:
            print("✅ URL is working!")
            return True
        else:
            print("❌ URL failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing URL: {e}")
        return False

def test_audiobook_api(user_id="test_user"):
    """Test the audiobook API endpoints"""
    base_url = "https://epub-audiobook-service-ab00bb696e09.herokuapp.com"
    
    print(f"Testing audiobook API for user: {user_id}")
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{base_url}/health")
        print(f"Health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test audiobooks list
    try:
        audiobooks_response = requests.get(f"{base_url}/api/audiobooks/{user_id}")
        print(f"Audiobooks list: {audiobooks_response.status_code}")
        
        if audiobooks_response.status_code == 200:
            data = audiobooks_response.json()
            audiobooks = data.get('audiobooks', [])
            print(f"Found {len(audiobooks)} audiobooks")
            
            # Test first audiobook's streaming URLs
            if audiobooks:
                audiobook = audiobooks[0]
                audiobook_id = audiobook['id']
                print(f"Testing audiobook: {audiobook['title']}")
                
                # Get audiobook details
                details_response = requests.get(f"{base_url}/api/download/{audiobook_id}")
                if details_response.status_code == 200:
                    details = details_response.json()
                    chapters = details.get('chapters', [])
                    print(f"Found {len(chapters)} chapters")
                    
                    # Test first chapter URL
                    if chapters:
                        chapter_url = chapters[0]['url']
                        print(f"Testing first chapter URL...")
                        test_streaming_url(chapter_url)
                else:
                    print(f"❌ Failed to get audiobook details: {details_response.status_code}")
            else:
                print("No audiobooks found to test")
        else:
            print(f"❌ Failed to get audiobooks: {audiobooks_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing audiobooks API: {e}")

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "test_user"
    test_audiobook_api(user_id)