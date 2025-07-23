#!/bin/bash

# Quick bot restart script with better error handling
echo "🤖 Restarting EPUB Audiobook Bot..."

# Check if token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Error: TELEGRAM_BOT_TOKEN environment variable not set"
    echo "Please run: export TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "Or create a .env file with your token"
    exit 1
fi

# Kill any existing processes
pkill -f "python.*bot.py" 2>/dev/null
pkill -f "python.*server.py" 2>/dev/null

# Wait a moment
sleep 2

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start server in background
echo "Starting server..."
python server.py &
SERVER_PID=$!

# Wait for server
sleep 2

# Start bot with error handling
echo "Starting bot..."
python bot.py 2>&1 | tee bot.log &
BOT_PID=$!

echo "✅ Bot restarted!"
echo "Server PID: $SERVER_PID"
echo "Bot PID: $BOT_PID"
echo "Check bot.log for any errors"

# Keep processes running
wait