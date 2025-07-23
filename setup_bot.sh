#!/bin/bash

# Telegram Bot Setup Script
echo "🤖 Telegram Bot Setup Guide"
echo "==========================="
echo ""

echo "📱 Step 1: Create Your Bot"
echo "1. Open Telegram and search for: @BotFather"
echo "2. Send: /newbot"
echo "3. Choose a name: EPUB Audiobook Bot"
echo "4. Choose username: epub_audiobook_bot (must end with 'bot')"
echo "5. Copy the token BotFather gives you"
echo ""

echo "🔑 Step 2: Set Your Token"
echo "Replace 'YOUR_TOKEN_HERE' with your actual token:"
echo ""
echo "export TELEGRAM_BOT_TOKEN='YOUR_TOKEN_HERE'"
echo ""
echo "Example:"
echo "export TELEGRAM_BOT_TOKEN='1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ-1234567890'"
echo ""

echo "✅ Step 3: Verify Setup"
echo "Check your token is set:"
echo "echo \$TELEGRAM_BOT_TOKEN"
echo ""

echo "🚀 Step 4: Start Your Bot"
echo "./start.sh"
echo ""

echo "📚 Step 5: Test with Z-Library"
echo "1. Get EPUB from Z-Library bot (as usual)"
echo "2. Forward that EPUB to YOUR bot (@your_bot_name)"
echo "3. Your bot converts it to audiobook"
echo "4. Listen in Android Auto!"
echo ""

echo "💡 Pro Tips:"
echo "• Your bot is completely separate from Z-Library"
echo "• You can forward EPUBs from any source to your bot"
echo "• Bot works with EPUBs from emails, downloads, etc."
echo "• Keep your token secret - don't share it"
echo ""

echo "🔧 Troubleshooting:"
echo "• Bot not responding? Check token is correct"
echo "• 'Unauthorized' error? Token might be wrong"
echo "• Can't find bot? Check username ends with 'bot'"
echo ""

# Check if token is already set
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✅ Token is already set!"
    echo "Current token: ${TELEGRAM_BOT_TOKEN:0:10}..."
else
    echo "⚠️ Token not set yet. Please run:"
    echo "export TELEGRAM_BOT_TOKEN='your_token_here'"
fi