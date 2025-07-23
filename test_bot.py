#!/usr/bin/env python3
"""
Test script to verify EPUB to Audiobook Bot functionality
"""

import asyncio
import sys
import os
from pathlib import Path
import tempfile
import zipfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_epub():
    """Create a minimal EPUB file for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    epub_path = temp_dir / "test_book.epub"
    
    # Create minimal EPUB structure
    with zipfile.ZipFile(epub_path, 'w') as epub:
        # mimetype (must be first, uncompressed)
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # META-INF/container.xml
        container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        epub.writestr('META-INF/container.xml', container_xml)
        
        # OEBPS/content.opf
        content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uuid_id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Audiobook</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="uuid_id">test-book-123</dc:identifier>
  </metadata>
  <manifest>
    <item href="chapter1.xhtml" id="chapter1" media-type="application/xhtml+xml"/>
    <item href="chapter2.xhtml" id="chapter2" media-type="application/xhtml+xml"/>
    <item href="toc.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
    <itemref idref="chapter2"/>
  </spine>
</package>'''
        epub.writestr('OEBPS/content.opf', content_opf)
        
        # OEBPS/toc.ncx
        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="test-book-123"/></head>
  <docTitle><text>Test Audiobook</text></docTitle>
  <navMap>
    <navPoint id="chapter1"><navLabel><text>Chapter 1</text></navLabel><content src="chapter1.xhtml"/></navPoint>
    <navPoint id="chapter2"><navLabel><text>Chapter 2</text></navLabel><content src="chapter2.xhtml"/></navPoint>
  </navMap>
</ncx>'''
        epub.writestr('OEBPS/toc.ncx', toc_ncx)
        
        # OEBPS/chapter1.xhtml
        chapter1 = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
<h1>Chapter 1: The Beginning</h1>
<p>This is the first chapter of our test audiobook. It contains enough text to verify that the text-to-speech conversion is working properly. The bot should be able to extract this text and convert it to audio using Microsoft Edge TTS.</p>
<p>We want to make sure that the EPUB parsing, text extraction, and audio generation pipeline all work correctly in our hobby project.</p>
</body>
</html>'''
        epub.writestr('OEBPS/chapter1.xhtml', chapter1)
        
        # OEBPS/chapter2.xhtml  
        chapter2 = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 2</title></head>
<body>
<h1>Chapter 2: The Test</h1>
<p>This is the second chapter of our test audiobook. If you can hear this being read aloud in your Android Auto car system, then congratulations - the complete pipeline from EPUB to car audio is working!</p>
<p>The system successfully processed the EPUB file, extracted the text, converted it to speech, and made it available in your car's media system.</p>
</body>
</html>'''
        epub.writestr('OEBPS/chapter2.xhtml', chapter2)
    
    logger.info(f"Created test EPUB: {epub_path}")
    return epub_path

async def test_bot_components():
    """Test individual bot components"""
    logger.info("🧪 Testing Bot Components...")
    
    try:
        # Test EPUB parsing
        logger.info("📚 Testing EPUB parsing...")
        epub_path = create_sample_epub()
        
        # Import bot modules
        sys.path.append(str(Path(__file__).parent))
        from bot import EpubAudiobookBot
        
        # Create temporary bot instance for testing
        bot = EpubAudiobookBot("dummy_token")
        
        # Test EPUB text extraction
        chapters = await bot.extract_epub_text(epub_path)
        if chapters:
            logger.info(f"✅ EPUB parsing works! Found {len(chapters)} chapters")
            for i, chapter in enumerate(chapters):
                logger.info(f"   Chapter {i+1}: {chapter['title'][:50]}...")
        else:
            logger.error("❌ EPUB parsing failed - no chapters found")
            return False
            
        # Test TTS conversion (with small sample)
        logger.info("🎙️ Testing TTS conversion...")
        test_chapters = [{"title": "Test Chapter", "text": "This is a test of the text to speech system."}]
        audio_files = await bot.convert_to_audio(test_chapters)
        
        if audio_files:
            logger.info(f"✅ TTS conversion works! Generated {len(audio_files)} audio files")
            for audio in audio_files:
                if Path(audio['path']).exists():
                    size = Path(audio['path']).stat().st_size
                    logger.info(f"   {audio['filename']}: {size} bytes")
                else:
                    logger.error(f"❌ Audio file not found: {audio['path']}")
                    return False
        else:
            logger.error("❌ TTS conversion failed")
            return False
            
        # Test podcast feed generation
        logger.info("📡 Testing podcast feed generation...")
        from podcast import PodcastGenerator
        podcast_gen = PodcastGenerator()
        
        feed_url = podcast_gen.create_user_feed(12345, "Test User")
        if feed_url:
            logger.info(f"✅ Podcast feed generation works! URL: {feed_url}")
        else:
            logger.error("❌ Podcast feed generation failed")
            return False
            
        logger.info("🎉 All bot components working!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}")
        return False

def test_server_endpoints():
    """Test Flask server endpoints"""
    logger.info("🌐 Testing Server Endpoints...")
    
    try:
        import requests
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Health endpoint working")
        else:
            logger.error(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
        # Test feed endpoint (will return 404 for non-existent user, but should respond)
        response = requests.get(f"{base_url}/feed/12345", timeout=5)
        if response.status_code in [200, 404]:
            logger.info("✅ Feed endpoint responding")
        else:
            logger.error(f"❌ Feed endpoint error: {response.status_code}")
            return False
            
        logger.info("🎉 Server endpoints working!")
        return True
        
    except ImportError:
        logger.info("ℹ️ requests module not available - skipping server tests")
        return True
    except Exception as e:
        logger.error(f"❌ Server test failed: {e}")
        logger.info("💡 Make sure to run './start_venv.sh' first to start the server")
        return True  # Don't fail the whole test suite for server issues

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("📦 Checking Dependencies...")
    
    required_modules = [
        'telegram', 'edge_tts', 'ebooklib',
        'feedgen', 'aiofiles', 'flask', 'qrcode'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module}")
        except ImportError:
            logger.error(f"❌ {module} - MISSING")
            missing.append(module)
    
    if missing:
        logger.error(f"❌ Missing dependencies: {missing}")
        logger.info("💡 Run: pip install -r requirements.txt")
        return False
    
    logger.info("🎉 All dependencies installed!")
    return True

def check_environment():
    """Check environment variables and configuration"""
    logger.info("🔧 Checking Environment...")
    
    # Check bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if bot_token:
        logger.info("✅ TELEGRAM_BOT_TOKEN is set")
    else:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set")
        logger.info("💡 Run: export TELEGRAM_BOT_TOKEN='your_bot_token'")
        return False
    
    # Check if podcasts directory exists
    podcasts_dir = Path("podcasts")
    if podcasts_dir.exists():
        logger.info("✅ Podcasts directory exists")
    else:
        logger.info("ℹ️ Creating podcasts directory...")
        podcasts_dir.mkdir(exist_ok=True)
    
    logger.info("🎉 Environment configured!")
    return True

async def run_full_test():
    """Run complete test suite"""
    logger.info("🚀 Starting Full Test Suite...")
    logger.info("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        return False
    
    # Step 2: Check environment  
    if not check_environment():
        return False
    
    # Step 3: Test bot components
    if not await test_bot_components():
        return False
    
    # Step 4: Test server (optional - might not be running)
    logger.info("\n" + "=" * 50)
    logger.info("🌐 Testing Server (optional)...")
    test_server_endpoints()  # Don't fail if server not running
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 ALL TESTS PASSED!")
    logger.info("\n📋 Next Steps:")
    logger.info("1. Start the bot: ./start.sh")
    logger.info("2. Send test EPUB to your bot in Telegram")
    logger.info("3. Check that MP3 files are generated")
    logger.info("4. Verify podcast feed is created")
    logger.info("5. Test Android Auto app integration")
    
    return True

if __name__ == "__main__":
    print("🧪 EPUB Audiobook Bot - Test Suite")
    print("=" * 50)
    
    try:
        result = asyncio.run(run_full_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)