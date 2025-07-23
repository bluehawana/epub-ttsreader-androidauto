# 🚀 Railway Deployment - Simple TTS + MP3 Service

## Why Railway is Perfect for Our Use Case

### ✅ **Simple Architecture:**
```
Telegram Bot → Railway App → Android Auto
     ↓              ↓              ↓
Send EPUB     TTS + Store MP3   Stream & Play
```

### 💰 **Cost: $5/month total**
- App hosting
- PostgreSQL database  
- File storage for MP3s
- Global bandwidth
- No surprise charges

### 🔧 **Technical Stack:**
- **Backend:** Python Flask (our existing code)
- **TTS:** Edge TTS (free, no API costs)
- **Storage:** Railway's built-in file system
- **Database:** PostgreSQL (user data, book metadata)
- **CDN:** Automatic global distribution

## 📁 Project Structure for Railway

```
epub-audiobook-cloud/
├── requirements.txt          # Python dependencies
├── main.py                  # Flask app (railway auto-detects)
├── Procfile                 # Optional: web: python main.py
├── railway.json             # Railway configuration
├── models/
│   ├── user.py             # User data models
│   └── audiobook.py        # Book metadata models
├── services/
│   ├── epub_processor.py   # EPUB → Text extraction
│   ├── tts_service.py      # Text → MP3 conversion
│   └── storage_service.py  # MP3 file management
└── api/
    ├── telegram_webhook.py # Receive from bot
    ├── android_auto.py     # Serve to car app
    └── auth.py            # User authentication
```

## 🌐 API Endpoints for Android Auto

```python
# For Android Auto app
GET  /api/audiobooks/{user_id}     # Get user's library
GET  /api/stream/{book_id}/{chapter} # Stream MP3 chapter
POST /api/sync                     # Check for new books
POST /api/auth                     # Authenticate car app

# For Telegram Bot  
POST /api/process-epub             # Upload EPUB for processing
GET  /api/status/{job_id}          # Check processing status
```

## 🔄 Simple Workflow

### **User Experience:**
1. **Forward EPUB** to Telegram bot
2. **Bot uploads** to Railway app
3. **Railway processes** EPUB → MP3 chapters
4. **Android Auto syncs** new book automatically
5. **Car displays** book with play/pause/next buttons

### **Processing Pipeline:**
```python
# Simplified processing (no complex queues needed)
def process_epub(epub_data, user_id):
    # 1. Extract text from EPUB
    chapters = extract_chapters(epub_data)
    
    # 2. Convert to speech (Edge TTS - free!)
    mp3_files = []
    for chapter in chapters:
        mp3_data = edge_tts.convert(chapter.text)
        mp3_path = save_mp3(mp3_data, user_id, chapter.id)
        mp3_files.append(mp3_path)
    
    # 3. Save to database
    audiobook = create_audiobook_record(user_id, chapters, mp3_files)
    
    # 4. Return success
    return audiobook.id
```

## 🚗 Android Auto Integration

### **Simple Media Player:**
- **Library screen** - List audiobooks with large touch buttons
- **Player screen** - Play/pause/next/previous/volume
- **Voice commands** - "Play my latest audiobook"
- **Background sync** - Check for new books every 30 seconds

### **API Calls from Car:**
```kotlin
// Android Auto app polls every 30 seconds
suspend fun syncAudiobooks() {
    val response = api.getAudiobooks(userId)
    if (response.newBooks > 0) {
        updateLocalLibrary(response.audiobooks)
        notifyUser("New audiobook available!")
    }
}
```

## 📈 Scaling (Later)

### **Current: Personal Use**
- 1 user (you)
- ~10 books/month
- Edge TTS (free)
- Railway $5/month

### **Future: Multiple Users**
- Add user management
- Implement usage limits
- Consider paid TTS for quality
- Still $5-20/month on Railway

## 🛠️ Deployment Steps

1. **Create Railway account** (free)
2. **Connect GitHub repo**
3. **Push code** → Auto-deploy
4. **Add environment variables** (Telegram token)
5. **Test with curl/Postman**
6. **Connect Android Auto app**

Railway handles everything else automatically! 🎯