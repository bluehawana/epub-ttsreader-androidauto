# 🧪 Testing Guide - How to Know It's Working

## 🚀 Quick Test Checklist

### ✅ Phase 1: Bot Testing
```bash
cd epub-to-audiobook-bot/
python test_bot.py
```

**Expected Output:**
```
🧪 EPUB Audiobook Bot - Test Suite
📦 Checking Dependencies...
✅ telegram ✅ edge_tts ✅ ebooklib ✅ pydub ✅ feedgen
🔧 Checking Environment...
✅ TELEGRAM_BOT_TOKEN is set
🧪 Testing Bot Components...
✅ EPUB parsing works! Found 2 chapters
✅ TTS conversion works! Generated 1 audio files
✅ Podcast feed generation works!
🎉 ALL TESTS PASSED!
```

### ✅ Phase 2: End-to-End Bot Test
```bash
# 1. Start the bot
./start.sh

# 2. In Telegram, send these commands:
/start          # Should show welcome message
/help           # Should show all commands  
/podcast        # Should return RSS feed URL
/linkcar        # Should show QR code image
/stats          # Should show 0 books initially
```

### ✅ Phase 3: EPUB Processing Test
1. **Send test EPUB** (created by test script) to your bot
2. **Watch for progress messages:**
   ```
   📖 Processing your EPUB file...
   📝 Extracting text from EPUB... 
   🎙️ Converting 2 chapters to audio...
   📡 Adding to your podcast feed...
   📤 Sending audiobook files...
   ✅ Audiobook conversion complete!
   ```
3. **Verify outputs:**
   - MP3 files sent to Telegram
   - Podcast feed updated
   - RSS feed accessible via URL

## 🚗 Android Auto App Testing

### ✅ Phase 1: App Installation
```bash
cd audiobook-car-player/
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

### ✅ Phase 2: QR Linking Test
1. **Open app** on phone
2. **Tap "Connect Telegram Bot"**
3. **In Telegram:** `/linkcar`
4. **Scan QR** with phone camera
5. **Verify:** App shows "Linked successfully"

### ✅ Phase 3: Android Auto Integration
1. **Connect phone** to Android Auto (USB/Wireless)
2. **Launch** "Audiobook Car Player" from car screen
3. **Verify screens:**
   - QR Login Screen (if not linked)
   - Library Screen (shows audiobooks)
   - Player Screen (playback controls)

## 🔍 Detailed Testing Scripts

### 🤖 Bot Component Tests

<function_calls>
<invoke name="Write">
<parameter name="content">#!/bin/bash

# Manual Bot Testing Script
echo "🤖 Manual Bot Testing Guide"
echo "=========================="

echo "1. 📋 Prerequisites Check:"
echo "   • Bot token set: $TELEGRAM_BOT_TOKEN"
echo "   • Dependencies installed: pip install -r requirements.txt"
echo ""

echo "2. 🚀 Start Bot:"
echo "   ./start.sh"
echo ""

echo "3. 📱 Telegram Commands to Test:"
echo "   /start    → Welcome message + commands list"
echo "   /help     → Feature description"  
echo "   /podcast  → Personal RSS feed URL"
echo "   /linkcar  → QR code for Android Auto"
echo "   /stats    → Usage statistics"
echo ""

echo "4. 📚 EPUB Upload Test:"
echo "   • Forward any .epub file to your bot"
echo "   • Watch for processing messages"
echo "   • Receive MP3 audio files"
echo "   • Check podcast feed updates"
echo ""

echo "5. 🔍 Verification Steps:"
echo "   • MP3 files play correctly"
echo "   • RSS feed XML is valid"
echo "   • Podcast contains new episodes"
echo "   • Progress tracking works"
echo ""

echo "6. 📡 Server Endpoints Test:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/feed/YOUR_USER_ID"
echo ""

echo "🎯 Success Indicators:"
echo "✅ Bot responds to all commands"
echo "✅ EPUB processing completes without errors"
echo "✅ MP3 files are generated and sent"
echo "✅ Podcast feed is accessible"
echo "✅ QR codes are generated for car linking"