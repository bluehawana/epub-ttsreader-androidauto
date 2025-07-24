#!/usr/bin/env python3
"""
Test script for EPUB to Audiobook Backend
Tests the complete flow: EPUB → TTS → R2 Storage
"""
import requests
import json
import base64
import time

# Your backend URL
BACKEND_URL = "https://epub-audiobook-service-ab00bb696e09.herokuapp.com"

def test_backend_health():
    """Test if backend is running"""
    print("🏥 Testing backend health...")
    response = requests.get(f"{BACKEND_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backend healthy: {data['status']}")
        print(f"📦 Storage: {data['storage']}")
        print(f"🎙️  TTS: {data['tts']}")
        return True
    else:
        print(f"❌ Backend unhealthy: {response.status_code}")
        return False

def create_test_epub():
    """Create a simple test EPUB as base64"""
    # Simple test content
    test_content = """
    <html>
    <head><title>Test Book</title></head>
    <body>
    <h1>Chapter 1: The Beginning</h1>
    <p>This is a test chapter to verify our EPUB to audiobook conversion system is working correctly. The text-to-speech system should convert this text into an MP3 file and store it in Cloudflare R2 storage.</p>
    
    <h1>Chapter 2: The Middle</h1>
    <p>This is the second chapter of our test book. It contains different text to ensure our system can handle multiple chapters and create separate audio files for each one.</p>
    </body>
    </html>
    """
    
    # For testing, we'll send the HTML content directly
    # In real implementation, this would be proper EPUB binary data
    return base64.b64encode(test_content.encode()).decode()

def test_epub_processing():
    """Test EPUB processing endpoint"""
    print("\n📚 Testing EPUB processing...")
    
    test_data = {
        "user_id": "test_user_123",
        "book_title": "Test Audiobook",
        "epub_data": create_test_epub()
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/process-epub",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Processing started: {data['job_id']}")
        print(f"📝 Status: {data['status']}")
        print(f"⏱️  Estimated time: {data['estimated_time']}")
        return data['job_id']
    else:
        print(f"❌ Processing failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_audiobook_list(user_id):
    """Test getting user's audiobook list"""
    print(f"\n📋 Testing audiobook list for user: {user_id}")
    
    response = requests.get(f"{BACKEND_URL}/api/audiobooks/{user_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} audiobooks")
        
        for book in data['audiobooks']:
            print(f"  📖 {book['title']} ({book['chapters']} chapters)")
            print(f"     ID: {book['id']}")
            print(f"     Created: {book['created_at']}")
        
        return data['audiobooks']
    else:
        print(f"❌ Failed to get audiobooks: {response.status_code}")
        return []

def test_download_links(audiobook_id):
    """Test getting download links for audiobook"""
    print(f"\n🔗 Testing download links for: {audiobook_id}")
    
    response = requests.get(f"{BACKEND_URL}/api/download/{audiobook_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Audiobook: {data['title']}")
        print(f"📊 Total chapters: {data['total_chapters']}")
        
        for chapter in data['chapters']:
            print(f"  🎵 Chapter {chapter['chapter']}: {chapter['title']}")
            print(f"     URL: {chapter['url']}")
            print(f"     Duration: {chapter['duration']}s")
        
        return data
    else:
        print(f"❌ Failed to get download links: {response.status_code}")
        return None

def main():
    """Run complete backend test"""
    print("🚀 Starting EPUB Audiobook Backend Test")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_backend_health():
        return
    
    # Test 2: Process test EPUB
    job_id = test_epub_processing()
    if not job_id:
        return
    
    # Test 3: Wait for processing (TTS takes time)
    print(f"\n⏳ Waiting for processing to complete...")
    print("This may take 2-5 minutes for TTS conversion...")
    
    # Wait and check periodically
    for i in range(30):  # Wait up to 5 minutes
        time.sleep(10)
        audiobooks = test_audiobook_list("test_user_123")
        
        if audiobooks:
            print(f"✅ Processing completed!")
            
            # Test 4: Get download links
            test_download_links(audiobooks[0]['id'])
            break
        else:
            print(f"⏳ Still processing... ({i*10}s)")
    
    print("\n🎉 Backend test completed!")

if __name__ == "__main__":
    main()