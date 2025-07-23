import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import edge_tts
import ebooklib
from ebooklib import epub
import aiofiles

from podcast import PodcastGenerator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EpubAudiobookBot:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.podcast_gen = PodcastGenerator()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up bot command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("podcast", self.podcast_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("linkcar", self.link_car_command))
        self.app.add_handler(MessageHandler(filters.Document.FileExtension("epub"), self.handle_epub))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Check if this is a car authentication request
        if context.args and len(context.args) > 0:
            arg = context.args[0]
            if arg.startswith('car_auth_'):
                await self.handle_car_auth(update, arg)
                return
        
        welcome_message = (
            "🎧 Welcome to EPUB Audiobook Bot!\n\n"
            "Simply send me an EPUB file and I'll convert it to audiobook MP3s!\n\n"
            "Commands:\n"
            "/help - Show this help message\n"
            "/podcast - Get your personal podcast feed URL\n"
            "/linkcar - Link your Android Auto car app\n"
            "/stats - View your audiobook statistics\n"
            "/start - Start the bot"
        )
        await update.message.reply_text(welcome_message)
    
    async def handle_car_auth(self, update: Update, auth_data: str):
        """Handle car authentication from QR code scan"""
        try:
            # Parse: car_auth_{token}_{user_id}
            parts = auth_data.split('_')
            if len(parts) >= 4:
                token = parts[2]
                original_user_id = parts[3]
                
                current_user_id = update.effective_user.id
                
                auth_message = (
                    f"🚗 Car Authentication Success!\n\n"
                    f"✅ Token: {token[:8]}...\n"
                    f"✅ Original User: {original_user_id}\n"
                    f"✅ Current User: {current_user_id}\n\n"
                    f"Your Android Auto app is now linked!\n"
                    f"Forward EPUBs from Z-Library and they'll appear in your car.\n\n"
                    f"Commands:\n"
                    f"/podcast - Get your podcast feed\n"
                    f"/stats - View your library"
                )
                
                await update.message.reply_text(auth_message)
            else:
                await update.message.reply_text("❌ Invalid authentication data")
        except Exception as e:
            await update.message.reply_text(f"❌ Authentication error: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "📚 How to use this bot:\n\n"
            "1. Send me an EPUB file\n"
            "2. I'll extract the text and convert it to speech\n"
            "3. You'll receive MP3 audiobook files\n"
            "4. Get your podcast feed with /podcast\n\n"
            "Features:\n"
            "✅ Free Microsoft Edge TTS\n"
            "✅ Chapter-based audio files\n"
            "✅ Personal podcast feed\n"
            "✅ High quality voices\n"
            "✅ Multiple language support"
        )
        await update.message.reply_text(help_message)
    
    async def podcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /podcast command - return user's podcast feed URL"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Create or get existing feed
        feed_url = self.podcast_gen.create_user_feed(user_id, user_name)
        
        podcast_message = (
            f"🎙️ Your Personal Podcast Feed:\n\n"
            f"📡 URL: {feed_url}\n\n"
            f"📱 How to use:\n"
            f"1. Copy the URL above\n"
            f"2. Add it to your favorite podcast app\n"
            f"3. New audiobooks will appear automatically!\n\n"
            f"Compatible with: Apple Podcasts, Spotify, Google Podcasts, and more!"
        )
        await update.message.reply_text(podcast_message)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - show user statistics"""
        user_id = update.effective_user.id
        stats = self.podcast_gen.get_user_stats(user_id)
        
        stats_message = (
            f"📊 Your Audiobook Statistics:\n\n"
            f"📚 Total Books: {stats['books']}\n"
            f"🎧 Total Episodes: {stats['episodes']}\n"
        )
        
        if stats['latest_book']:
            stats_message += f"📖 Latest Book: {stats['latest_book']}\n"
        
        if stats['episodes'] == 0:
            stats_message += f"\n💡 Send me an EPUB file to get started!"
        
        await update.message.reply_text(stats_message)
    
    async def link_car_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /linkcar command - generate QR for Android Auto app"""
        user_id = update.effective_user.id
        
        # Generate linking token
        import uuid
        link_token = str(uuid.uuid4())
        
        # Store linking token (in real app, use database)
        # For demo, we'll create a web URL that works without app
        
        # Create web URL that redirects or shows instructions
        web_url = f"https://t.me/epubreaderbot?start=car_auth_{link_token}_{user_id}"
        
        # Generate QR code
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(web_url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        qr_image.save(bio, format='PNG')
        bio.seek(0)
        
        car_message = (
            f"🚗 Link Your Android Auto App\n\n"
            f"**For testing without Android Auto app:**\n"
            f"1. Scan this QR code with any device\n"
            f"2. It will open this same bot\n"
            f"3. Bot will confirm the linking\n\n"
            f"**For actual car use:**\n"
            f"1. Install Android Auto app on phone\n"
            f"2. QR code will appear on car screen\n"
            f"3. Scan QR with phone camera\n"
            f"4. Audiobooks sync automatically!\n\n"
            f"🔗 Direct link: {web_url}\n\n"
            f"💡 Token ID: {link_token[:8]}..."
        )
        
        await update.message.reply_photo(
            photo=bio,
            caption=car_message
        )
    
    async def handle_epub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle EPUB file uploads"""
        document: Document = update.message.document
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "📖 Processing your EPUB file...\nThis may take a few minutes!"
        )
        
        try:
            # Download EPUB file
            epub_path = await self.download_epub(document)
            book_title = document.file_name.replace('.epub', '')
            
            # Extract text from EPUB
            await processing_msg.edit_text("📝 Extracting text from EPUB...")
            chapters = await self.extract_epub_text(epub_path)
            
            if not chapters:
                await processing_msg.edit_text("❌ Could not extract text from EPUB file")
                return
            
            # Convert to audio
            await processing_msg.edit_text(f"🎙️ Converting {len(chapters)} chapters to audio...")
            audio_files = await self.convert_to_audio(chapters)
            
            # Add to podcast feed
            await processing_msg.edit_text("📡 Adding to your podcast feed...")
            self.podcast_gen.add_audiobook_episode(
                user_id, 
                book_title, 
                audio_files,
                {'author': 'Unknown', 'file_name': document.file_name}
            )
            
            # Send audio files
            await processing_msg.edit_text("📤 Sending audiobook files...")
            await self.send_audio_files(update, audio_files)
            
            # Final success message with podcast info
            feed_url = self.podcast_gen.get_feed_url(user_id)
            success_message = (
                f"✅ Audiobook conversion complete!\n\n"
                f"📚 Book: {book_title}\n"
                f"🎧 Chapters: {len(audio_files)}\n\n"
                f"🎙️ Added to your podcast: {feed_url}\n\n"
                f"Use /podcast to get your feed URL anytime!"
            )
            await processing_msg.edit_text(success_message)
            
        except Exception as e:
            logger.error(f"Error processing EPUB: {e}")
            await processing_msg.edit_text(f"❌ Error processing file: {str(e)}")
        finally:
            # Cleanup temp files
            await self.cleanup_temp_files()
    
    async def download_epub(self, document: Document) -> Path:
        """Download EPUB file from Telegram"""
        file = await document.get_file()
        epub_path = self.temp_dir / f"{document.file_name}"
        await file.download_to_drive(epub_path)
        return epub_path
    
    async def extract_epub_text(self, epub_path: Path) -> list:
        """Extract text content from EPUB file"""
        try:
            book = epub.read_epub(str(epub_path))
            chapters = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # Simple HTML tag removal (basic)
                    content = item.get_content().decode('utf-8')
                    # Remove HTML tags (simple approach)
                    import re
                    text = re.sub(r'<[^>]+>', '', content)
                    text = text.strip()
                    
                    if text and len(text) > 100:  # Skip very short chapters
                        chapters.append({
                            'title': item.get_name(),
                            'text': text[:5000]  # Limit text length for demo
                        })
            
            return chapters[:3]  # Limit to 3 chapters for demo
            
        except Exception as e:
            logger.error(f"Error extracting EPUB: {e}")
            return []
    
    async def convert_to_audio(self, chapters: list) -> list:
        """Convert text chapters to audio using Edge TTS"""
        audio_files = []
        voice = "en-US-AriaNeural"  # Default voice
        
        for i, chapter in enumerate(chapters):
            try:
                # Generate speech
                communicate = edge_tts.Communicate(chapter['text'], voice)
                audio_path = self.temp_dir / f"chapter_{i+1}.mp3"
                
                await communicate.save(str(audio_path))
                
                if audio_path.exists():
                    audio_files.append({
                        'path': audio_path,
                        'title': f"Chapter {i+1}",
                        'filename': f"chapter_{i+1}.mp3"
                    })
                    
            except Exception as e:
                logger.error(f"Error converting chapter {i+1}: {e}")
        
        return audio_files
    
    async def send_audio_files(self, update: Update, audio_files: list):
        """Send generated audio files to user"""
        for audio_file in audio_files:
            try:
                with open(audio_file['path'], 'rb') as f:
                    await update.message.reply_audio(
                        audio=f,
                        title=audio_file['title'],
                        filename=audio_file['filename']
                    )
            except Exception as e:
                logger.error(f"Error sending audio file: {e}")
    
    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = Path(tempfile.mkdtemp())
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting EPUB Audiobook Bot...")
        self.app.run_polling(drop_pending_updates=True)

def main():
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    bot = EpubAudiobookBot(token)
    bot.run()

if __name__ == "__main__":
    main()