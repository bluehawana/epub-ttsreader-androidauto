# EPUB to Audiobook Telegram Bot

A simple hobby project that converts EPUB files to audiobook MP3s using free Microsoft Edge TTS.

## Features

- 🤖 Telegram bot interface
- 📚 EPUB file processing
- 🎙️ Free text-to-speech (Microsoft Edge TTS)  
- 🎧 Chapter-based MP3 generation
- 📱 Easy file sharing via Telegram

## Setup

1. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Create new bot with `/newbot`
   - Save your bot token

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

1. Send `/start` to your bot
2. Upload an EPUB file  
3. Wait for processing
4. Receive MP3 audiobook files!

## Tech Stack

- **Bot Framework**: python-telegram-bot
- **EPUB Processing**: ebooklib
- **Text-to-Speech**: edge-tts (free Microsoft TTS)
- **Audio Processing**: pydub
- **Language**: Python 3.8+

## Limitations (Demo Version)

- Processes first 3 chapters only
- 5000 character limit per chapter
- Basic HTML tag removal
- English voice only (easily expandable)

## Future Enhancements

- Voice selection menu
- Full book processing
- Podcast RSS feed generation
- Chapter progress tracking
- Multiple language support