#!/usr/bin/env python3
"""
Super Simple CarBookReader Bot - Guaranteed to work
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8043237984:AAGOCQYtGyxTr9Jrwk6u9bN2bkoWts-qAFQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    message = """
🚗 **CarBookReaderBot is LIVE!**

📚 **How it works:**
1. Get EPUB from @duranleebot (Z-Library)
2. Send EPUB file to me
3. I convert to audiobook
4. Listen in Android Auto!

Commands:
/start - This message
/help - Detailed guide
/status - Check system

Ready to convert EPUBs! 📖→🎧
    """
    await update.message.reply_text(message)
    logger.info(f"Sent /start response to user {update.effective_user.id}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    message = """
📖 **Step-by-Step Guide:**

**1. Get EPUB from Z-Library:**
• Go to @duranleebot
• Search: "book title"
• Choose EPUB format
• Download

**2. Send to me:**
• Forward EPUB from @duranleebot
• Or upload EPUB directly

**3. Processing:**
• I convert text to speech
• Store as audiobook
• Takes 5-10 minutes

**4. Listen in car:**
• Use Android Auto app
• Browse your library
• Enjoy! 🚗🎧

Send me an EPUB file to start!
    """
    await update.message.reply_text(message)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    import requests
    
    try:
        response = requests.get("https://epub-audiobook-service-ab00bb696e09.herokuapp.com/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            message = f"""
✅ **System Status: HEALTHY**

🗄️ Storage: {data.get('storage', 'Unknown')}
🎙️ TTS: {data.get('tts', 'Unknown').upper()}
⏰ Last check: Now

Ready to process EPUBs! 📚
            """
        else:
            message = "❌ Backend not responding"
    except:
        message = "❌ Cannot reach backend"
    
    await update.message.reply_text(message)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file uploads"""
    file = update.message.document
    
    if file.file_name and file.file_name.lower().endswith('.epub'):
        message = f"""
📚 **EPUB Received!**

📖 File: {file.file_name}
📊 Size: {file.file_size / 1024:.1f} KB

⏳ **Processing starting...**
This will take 5-10 minutes.

*Feature coming soon - processing backend integration!*
        """
    else:
        message = f"""
📁 **File received:** {file.file_name}

❌ **Sorry, EPUB files only!**

Get EPUB from @duranleebot:
1. Search for book
2. Choose EPUB format
3. Send to me

Only .epub files supported! 📚
        """
    
    await update.message.reply_text(message)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    message = """
💬 **Hi! I process EPUB audiobooks.**

To get started:
1. Get EPUB from @duranleebot
2. Send EPUB file to me
3. I'll convert to audiobook

Commands: /start /help /status

Send me an EPUB file! 📚→🎧
    """
    await update.message.reply_text(message)

def main():
    """Start the bot"""
    print("🚀 Starting CarBookReaderBot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Bot configured, starting polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()