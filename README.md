# EPUB to Audiobook Service

A cloud-based service that converts EPUB files to audiobooks using Microsoft Azure TTS, designed for Android Auto integration.

## 🚀 Quick Deploy to Heroku

1. **Prerequisites:**
   ```bash
   # Install Heroku CLI
   brew tap heroku/brew && brew install heroku
   
   # Login to Heroku
   heroku login
   ```

2. **Deploy:**
   ```bash
   ./deploy.sh
   ```

3. **Set your API keys:**
   ```bash
   # Azure Speech Services (get from Azure Portal)
   heroku config:set AZURE_SPEECH_KEY=your_key_here --app epub-audiobook-service
   heroku config:set AZURE_SPEECH_REGION=eastus --app epub-audiobook-service
   
   # Your Telegram Bot Token
   heroku config:set TELEGRAM_BOT_TOKEN=your_token_here --app epub-audiobook-service
   ```

## 📱 Android Auto Integration

The service provides REST API endpoints for Android Auto apps:

- `GET /api/audiobooks/{user_id}` - Get user's audiobook library
- `GET /api/stream/{book_id}?chapter=1` - Stream audiobook chapters
- `POST /api/process-epub` - Convert new EPUB to audiobook

## 🎵 TTS Features

- **Primary:** Microsoft Azure Neural Voices (high quality)
- **Fallback:** Edge TTS (free backup)
- **Voices:** en-US-AriaNeural, en-US-JennyNeural, en-US-GuyNeural
- **Cost Estimation:** 500K characters free/month, then $4/1M chars

## 💾 Architecture

```
Telegram Bot → Heroku API → Azure TTS → R2 Storage → Android Auto
```

- **Database:** PostgreSQL (audiobooks, chapters, users)
- **Storage:** Cloudflare R2 (migrated from S3 for cost optimization)
- **Processing:** Async EPUB → MP3 conversion
- **Authentication:** QR code linking for Android Auto

## 🔧 Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run locally
python3 main.py

# OR use the provided startup script
chmod +x start_epub_reader.sh
./start_epub_reader.sh
```

## 📖 EPUB Reader (PS4 Compatible)

Access the web-based EPUB reader at: http://localhost:8000/reader

Features:
- Upload and read EPUB files directly in browser
- PS4 controller support (D-pad navigation)
- Chapter-by-chapter reading
- Responsive design for TV screens

## 🤖 Android App Testing

### Firebase Integration
The Android app now includes Firebase integration for enhanced analytics and testing:

1. **Setup Firebase:**
   - Added Google Services plugin to both root and app-level build.gradle
   - Configured Firebase BoM (Bill of Materials) for dependency management
   - Added `google-services.json` configuration file

2. **Building APK for Testing:**
   ```bash
   cd AudiobookPlayer
   ./gradlew assembleDebug  # Creates app-debug.apk for testing
   ```

3. **Testing on Physical Devices:**
   - Successfully tested on OnePlus devices
   - Firebase Test Lab integration available
   - Supports Telegram ID authentication for audiobook synchronization

### Device Compatibility
- ✅ **PS4 Emulator** - Full functionality confirmed
- ✅ **OnePlus Devices** - Successfully tested with Firebase
- ✅ **Android Auto** - Primary target platform
- 🔄 **Firebase Test Lab** - Available for automated testing

## 📊 Monitoring

```bash
# View logs
heroku logs --tail --app epub-audiobook-service

# Check health
curl https://epub-audiobook-service.herokuapp.com/health

# Firebase Analytics
# Available through Firebase Console for app usage tracking
```