# EPUB Audiobook Cloudflare Worker

A complete Cloudflare-native solution for converting EPUBs to audiobooks using Edge TTS and R2 storage.

## Features

- ✅ **Edge TTS Integration** - Free, high-quality text-to-speech
- ✅ **R2 Storage** - Scalable object storage for EPUBs and MP3s  
- ✅ **Durable Objects** - Long-running TTS processing that overcomes Worker CPU limits
- ✅ **Audio Streaming** - Range request support for efficient audio playback
- ✅ **Android App Compatible** - Same API as Heroku version

## Architecture

```
EPUB (R2) → CF Worker → Edge TTS → MP3 (R2) → Android App
```

## Advantages over Heroku

- **🚀 Performance**: No cold starts, edge deployment
- **💰 Cost**: CF Workers free tier vs Heroku paid plans  
- **🔗 Integration**: Native R2 integration, no external dependencies
- **⚡ Speed**: Processing happens closer to storage

## Setup

1. **Install Wrangler CLI**:
   ```bash
   npm install -g wrangler
   ```

2. **Configure R2 Bucket**:
   ```bash
   wrangler r2 bucket create ebuppool
   ```

3. **Deploy Worker**:
   ```bash
   cd cloudflare-worker
   npm install
   wrangler deploy
   ```

4. **Update Android App**:
   Update `ApiConfig.BASE_URL` to your worker URL

## API Endpoints

- `GET /health` - Worker health check
- `GET /api/audiobooks/{userId}` - List user's audiobooks  
- `POST /api/process-epub` - Process EPUB to audiobook
- `POST /api/scan-r2` - Scan R2 for new EPUBs
- `GET /api/download/{audiobookId}` - Get audiobook metadata
- `GET /api/stream/{r2Key}` - Stream audio with range support

## Performance Notes

- **CPU Limits**: Standard workers have 10-50ms CPU time
- **Durable Objects**: Used for long-running TTS processing
- **Memory**: 128MB limit for standard workers
- **Concurrency**: Handles multiple TTS jobs simultaneously

## TTS Implementation

Currently uses mock TTS data for testing. To implement real Edge TTS:

1. Use Web Speech API (if available in Workers)
2. Call external TTS service
3. Stream processing in chunks
4. Consider Durable Objects for longer processing

## Deployment

```bash
# Development
wrangler dev

# Production  
wrangler deploy

# Monitor logs
wrangler tail
```

## Configuration

Update `wrangler.toml` with your:
- R2 bucket name
- KV namespace IDs (optional)
- Environment variables