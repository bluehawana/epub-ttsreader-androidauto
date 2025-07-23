#!/bin/bash

# Start both bot and server with virtual environment
echo "Starting EPUB Audiobook Bot with Podcast Server..."

# Check if bot token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN environment variable not set"
    echo "Please run: export TELEGRAM_BOT_TOKEN='your_bot_token'"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if venv is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "✅ Virtual environment active: $VIRTUAL_ENV"

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