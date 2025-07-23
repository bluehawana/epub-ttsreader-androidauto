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
Telegram Bot → Heroku API → Azure TTS → S3 Storage → Android Auto
```

- **Database:** PostgreSQL (audiobooks, chapters, users)
- **Storage:** AWS S3 via Bucketeer addon
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
python main.py
```

## 📊 Monitoring

```bash
# View logs
heroku logs --tail --app epub-audiobook-service

# Check health
curl https://epub-audiobook-service.herokuapp.com/health
```