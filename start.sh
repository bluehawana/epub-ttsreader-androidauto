#!/bin/bash

# Start both bot and server
echo "Starting EPUB Audiobook Bot with Podcast Server..."

# Check if bot token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN environment variable not set"
    echo "Please run: export TELEGRAM_BOT_TOKEN='your_bot_token'"
    exit 1
fi

# Start Flask server in background
echo "Starting podcast server on port 8000..."
python server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Start Telegram bot
echo "Starting Telegram bot..."
python bot.py

# Clean up server process on exit
trap "kill $SERVER_PID 2>/dev/null" EXIT