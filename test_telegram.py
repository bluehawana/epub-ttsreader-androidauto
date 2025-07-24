#!/usr/bin/env python3
"""
Telegram Bot Testing Script
Tests integration between your Telegram bot and the backend API
"""
import requests
import json

def test_telegram_integration():
    """Test if Telegram bot can send data to backend"""
    print("🤖 Testing Telegram Bot Integration")
    print("=" * 40)
    
    # This simulates what your Telegram bot should send
    test_payload = {
        "user_id": "your_telegram_user_id",  # Replace with your Telegram user ID
        "book_title": "Test Book from Telegram",
        "epub_data": "PGh0bWw+PGhlYWQ+PHRpdGxlPlRlc3QgQm9vazwvdGl0bGU+PC9oZWFkPjxib2R5PjxoMT5DaGFwdGVyIDE6IFRlc3QgQ2hhcHRlcjwvaDE+PHA+VGhpcyBpcyBhIHRlc3QgY2hhcHRlciB0byB2ZXJpZnkgb3VyIEVQVUIgdG8gYXVkaW9ib29rIGNvbnZlcnNpb24gc3lzdGVtIGlzIHdvcmtpbmcgY29ycmVjdGx5LjwvcD48L2JvZHk+PC9odG1sPg=="
    }
    
    print("📤 Sending test data to backend...")
    print(f"User ID: {test_payload['user_id']}")
    print(f"Book Title: {test_payload['book_title']}")
    
    try:
        response = requests.post(
            "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/api/process-epub",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend accepted the request!")
            print(f"🆔 Job ID: {data.get('job_id')}")
            print(f"📝 Status: {data.get('status')}")
            return True
        else:
            print("❌ Backend rejected the request")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_bot_steps():
    """Show steps to test your actual Telegram bot"""
    print("\n🔧 How to Test Your Actual Telegram Bot:")
    print("=" * 40)
    print("1. Update your bot.py with the backend URL:")
    print("   BACKEND_URL = 'https://epub-audiobook-service-ab00bb696e09.herokuapp.com'")
    print("")
    print("2. In your bot, add code to send EPUB to backend:")
    print("""
    async def handle_epub(update, context):
        # Get EPUB file from user
        file = await context.bot.get_file(update.message.document.file_id)
        epub_bytes = await file.download_as_bytearray()
        epub_b64 = base64.b64encode(epub_bytes).decode()
        
        # Send to backend
        payload = {
            'user_id': str(update.effective_user.id),
            'book_title': update.message.document.file_name,
            'epub_data': epub_b64
        }
        
        response = requests.post(f'{BACKEND_URL}/api/process-epub', json=payload)
        # Handle response...
    """)
    print("")
    print("3. Test by sending an EPUB file to your bot")
    print("4. Check backend logs: heroku logs --tail --app epub-audiobook-service")

if __name__ == "__main__":
    test_telegram_integration()
    test_bot_steps()