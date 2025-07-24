#!/usr/bin/env python3
"""
Updated CarBookReaderBot to handle EPUB files from Z-Library
Processes EPUBs and sends to backend for TTS conversion
"""
import logging
import asyncio
import base64
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token and backend URL
BOT_TOKEN = "8043237984:AAGOCQYtGyxTr9Jrwk6u9bN2bkoWts-qAFQ"
BACKEND_URL = "https://epub-audiobook-service-ab00bb696e09.herokuapp.com"

class CarBookReaderBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up bot command and message handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
        # File handlers - handle EPUB files based on filename
        self.app.add_handler(MessageHandler(filters.Document.FileExtension("epub"), self.handle_epub_file))
        self.app.add_handler(MessageHandler(filters.Document.ALL & ~filters.Document.FileExtension("epub"), self.handle_other_files))
        
        # Text messages
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🚗 **CarBookReaderBot** - EPUB to Audiobook for Android Auto

**How to use:**
1. Get EPUB files from @duranleebot (Z-Library)
2. Forward or send EPUB files to me
3. I'll convert them to audiobooks for your car!

**Commands:**
/help - Show this help
/status - Check backend status

**Ready to convert your EPUBs! 📚→🎧**
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **How to get books:**

1. **Get EPUB from Z-Library:**
   - Go to @duranleebot
   - Search for book: "The Great Gatsby"
   - Choose EPUB format
   - Download file

2. **Send to me:**
   - Forward EPUB file from @duranleebot
   - Or upload EPUB file directly
   - I'll process it automatically!

3. **Listen in your car:**
   - Use Android Auto app
   - Browse your audiobook library
   - Enjoy hands-free listening! 🚗

**Supported:** EPUB files only
**Processing time:** 5-10 minutes per book
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check backend status"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status_msg = f"""
✅ **Backend Status: {data['status'].upper()}**
🗄️ Storage: {data['storage']}
🎙️ TTS: {data['tts'].upper()}
⏰ Last check: {data['timestamp']}

Ready to process your EPUBs! 📚
                """
            else:
                status_msg = "❌ Backend is not responding"
        except Exception as e:
            status_msg = f"❌ Cannot reach backend: {str(e)}"
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
    
    async def handle_epub_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle EPUB file uploads"""
        try:
            file = update.message.document
            user = update.effective_user
            
            # Send processing message
            processing_msg = await update.message.reply_text(
                f"📚 **Processing EPUB:** {file.file_name}\n"
                f"📊 **Size:** {file.file_size / 1024:.1f} KB\n"
                f"⏳ **Status:** Downloading and converting...\n\n"
                f"This will take 5-10 minutes. I'll notify you when done! 🎧",
                parse_mode='Markdown'
            )
            
            # Download file
            logger.info(f"Downloading EPUB: {file.file_name} from user {user.id}")
            file_obj = await context.bot.get_file(file.file_id)
            epub_bytes = await file_obj.download_as_bytearray()
            
            # Convert to base64
            epub_b64 = base64.b64encode(epub_bytes).decode()
            
            # Send to backend
            payload = {
                "user_id": str(user.id),
                "book_title": file.file_name.replace('.epub', ''),
                "epub_data": epub_b64
            }
            
            logger.info(f"Sending to backend: {len(epub_b64)} chars")
            response = requests.post(
                f"{BACKEND_URL}/api/process-epub",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                success_msg = f"""
✅ **EPUB Accepted for Processing!**

📖 **Book:** {file.file_name}
🆔 **Job ID:** {data['job_id']}
⏱️ **Estimated Time:** {data['estimated_time']}

I'll convert this to audiobook format and store it in your library. 
Use your Android Auto app to listen! 🚗🎧

*Processing in background...*
                """
                await context.bot.edit_message_text(
                    text=success_msg,
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg.message_id,
                    parse_mode='Markdown'
                )
                
                logger.info(f"Successfully sent EPUB to backend: {data['job_id']}")
                
            else:
                error_msg = f"❌ **Processing Failed**\n\nBackend error: {response.status_code}\n{response.text}"
                await context.bot.edit_message_text(
                    text=error_msg,
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg.message_id,
                    parse_mode='Markdown'
                )
                logger.error(f"Backend error: {response.status_code} - {response.text}")
                
        except Exception as e:
            error_msg = f"❌ **Error processing EPUB**\n\n{str(e)}"
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            logger.error(f"EPUB processing error: {e}")
    
    async def handle_other_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-EPUB files"""
        file = update.message.document
        file_type = file.mime_type or "unknown"
        
        message = f"""
📁 **File Received:** {file.file_name}
🏷️ **Type:** {file_type}

❌ **Sorry, I only process EPUB files!**

**To get EPUB files:**
1. Go to @duranleebot (Z-Library bot)
2. Search for your book
3. Choose **EPUB format** (not PDF)
4. Forward the EPUB file to me

**Supported format:** .epub only 📚
        """
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        message = """
💬 **Text message received!**

I'm designed to process EPUB audiobooks. Here's how:

1. **Get EPUB from Z-Library:**
   - Message @duranleebot
   - Search: "book title" or "author name"
   - Download EPUB format

2. **Send EPUB to me:**
   - Forward EPUB file from @duranleebot
   - Or upload EPUB directly

3. **Listen in Android Auto! 🚗**

Send me an EPUB file to get started! 📚
        """
        await update.message.reply_text(message, parse_mode='Markdown')
    
    def run(self):
        """Start the bot"""
        logger.info("Starting CarBookReaderBot...")
        logger.info(f"Backend URL: {BACKEND_URL}")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = CarBookReaderBot()
    bot.run()