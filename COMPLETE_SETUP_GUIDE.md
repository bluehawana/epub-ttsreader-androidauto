# 📱 Complete Setup Guide: Z-Library → CarBookReaderBot → Android Auto

## 🚀 Quick Start (5 minutes)

### 1. **Start Your Bot**
```bash
cd /Users/bluehawana/Projects/epub-to-audiobook-bot/
python3 carbookreader_bot.py
```

### 2. **Get EPUB from Z-Library Bot**
1. Open Telegram
2. Search: `@duranleebot` (ID: 5918214030)
3. Send: `/start`
4. Search for book: `"The Great Gatsby"` (or any book)
5. Choose **EPUB format** (not PDF!)
6. Download the file

### 3. **Send to Your Bot**
1. Forward EPUB from @duranleebot to @carbookreaderbot
2. Or go to @carbookreaderbot and upload EPUB directly
3. Bot will confirm: "✅ EPUB Accepted for Processing!"

### 4. **Wait for Processing** (5-10 minutes)
- Backend converts EPUB to audiobook
- Text-to-Speech generates MP3 files
- Files stored in Cloudflare R2

### 5. **Listen in Android Auto**
- Update Android app with: `https://epub-audiobook-service-ab00bb696e09.herokuapp.com`
- Browse audiobooks library
- Play your converted book! 🎧

## 🔧 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | Detailed usage guide |
| `/status` | Check backend service status |

## 📚 Supported Workflow

```
Z-Library Bot (@duranleebot) 
    ↓ (EPUB file)
CarBookReaderBot (@carbookreaderbot)
    ↓ (API call)
Backend (Heroku + R2)
    ↓ (TTS processing)
Android Auto App
    ↓ (Audio streaming)
Car Speakers 🔊
```

## ✅ Testing Checklist

- [ ] Z-Library bot responds to searches
- [ ] EPUB files download successfully  
- [ ] CarBookReaderBot receives and processes EPUBs
- [ ] Backend converts text to speech
- [ ] R2 storage contains MP3 files
- [ ] Android Auto app fetches audiobooks
- [ ] Audio plays smoothly in car

## 🐛 Troubleshooting

**"Bot not responding":**
```bash
# Check if bot is running
ps aux | grep carbookreader_bot.py

# Check backend health
curl "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/health"
```

**"EPUB processing failed":**
```bash
# Check Heroku logs
heroku logs --tail --app epub-audiobook-service
```

**"No audiobooks in Android app":**
- Verify user_id matches your Telegram ID
- Check if processing completed (wait 10 minutes)
- Test API directly: `/api/audiobooks/YOUR_TELEGRAM_ID`

Your system is ready to convert Z-Library EPUBs to car audiobooks! 🚗📚🎧