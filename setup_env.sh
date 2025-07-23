#!/bin/bash

# 🔒 SECURE Token Setup Script
echo "🔐 Setting up secure environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your bot token!"
    echo "   Your token: 8043237984:AAGOCQYtGyxTr9Jrwk6u9bN2bkoWts-qAFQ"
    echo ""
    echo "Steps:"
    echo "1. nano .env"
    echo "2. Replace YOUR_BOT_TOKEN_HERE with your actual token"
    echo "3. Save and exit"
    echo ""
    exit 1
fi

# Load environment variables
echo "Loading environment variables from .env..."
source .env

# Verify token is set
if [ "$TELEGRAM_BOT_TOKEN" = "YOUR_BOT_TOKEN_HERE" ] || [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Error: Please edit .env file and set your actual bot token"
    echo "Current token: $TELEGRAM_BOT_TOKEN"
    exit 1
fi

echo "✅ Environment configured securely!"
echo "Token set: ${TELEGRAM_BOT_TOKEN:0:10}..."

# Export for current session
export TELEGRAM_BOT_TOKEN
export SERVER_HOST="${SERVER_HOST:-localhost}"
export SERVER_PORT="${SERVER_PORT:-8000}"

echo "Ready to start bot!"