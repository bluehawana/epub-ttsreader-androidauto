#!/usr/bin/env python3
"""
Simple debug version of the bot to test basic connectivity and R2 upload
"""
import logging
import os
import boto3
import tempfile
import base64
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8043237984:AAGOCQYtGyxTr9Jrwk6u9bN2bkoWts-qAFQ"

def get_r2_client():
    """Get Cloudflare R2 client"""
    r2_endpoint = os.environ.get('R2_ENDPOINT_URL')
    r2_access_key = os.environ.get('R2_ACCESS_KEY_ID')
    r2_secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
    r2_bucket = os.environ.get('R2_BUCKET_NAME')
    
    if r2_endpoint and r2_access_key and r2_secret_key:
        r2 = boto3.client(
            's3',
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            region_name='auto'  # Cloudflare R2 uses 'auto'
        )
        return r2, r2_bucket
    return None, None

async def upload_epub_to_r2(file_path: str, user_id: str, file_name: str) -> str:
    """Upload EPUB file to Cloudflare R2"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            logger.warning("R2 not configured")
            return "❌ R2 storage not configured"
        
        # Create R2 key
        r2_key = f"{user_id}/epubs/{file_name}"
        
        # Upload to R2
        r2.upload_file(file_path, bucket_name, r2_key)
        
        # Create public URL
        url = f"https://pub-{bucket_name}.r2.dev/{r2_key}"
        logger.info(f"Uploaded {file_name} to R2: {url}")
        
        return f"✅ Uploaded to R2!\n🔗 {url}"
        
    except Exception as e:
        logger.error(f"R2 upload failed: {e}")
        return f"❌ Upload failed: {str(e)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple start command"""
    logger.info(f"Received /start from user {update.effective_user.id}")
    await update.message.reply_text("🎉 Bot is working! I can see your /start command!")

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message"""
    if update.message.document:
        file_name = update.message.document.file_name
        user_id = str(update.effective_user.id)
        logger.info(f"Received file: {file_name} from user {user_id}")
        
        if file_name and file_name.lower().endswith('.epub'):
            # Send processing message
            processing_msg = await update.message.reply_text(f"📚 EPUB received: {file_name}\n⏳ Uploading to R2 storage...")
            
            try:
                # Download file from Telegram
                file = await update.message.document.get_file()
                
                # Create temp file
                with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_file:
                    await file.download_to_drive(tmp_file.name)
                    temp_path = tmp_file.name
                
                # Upload to R2
                result = await upload_epub_to_r2(temp_path, user_id, file_name)
                
                # Update message with result
                await processing_msg.edit_text(f"📚 EPUB: {file_name}\n{result}")
                
                # Cleanup temp file
                os.unlink(temp_path)
                
            except Exception as e:
                logger.error(f"File processing error: {e}")
                await processing_msg.edit_text(f"📚 EPUB: {file_name}\n❌ Upload failed: {str(e)}")
        else:
            await update.message.reply_text(f"📁 File received: {file_name}\n❌ Only EPUB files supported!")
    elif update.message.text:
        logger.info(f"Received message: {update.message.text} from user {update.effective_user.id}")
        await update.message.reply_text(f"I received: {update.message.text}")
    else:
        logger.info(f"Received unknown message type from user {update.effective_user.id}")
        await update.message.reply_text("I received a message but couldn't process it.")

def main():
    """Start the debug bot"""
    logger.info("Starting DEBUG bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.ALL, any_message))
    
    # Start polling
    logger.info("Bot is running and polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()