import os
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
from pathlib import Path
import tempfile
import uuid
from datetime import datetime
import pymysql
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError

# Import our services
from azure_tts import AzureTTSService
from bot import EpubAudiobookBot
from podcast import PodcastGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
tts_service = AzureTTSService()
podcast_gen = PodcastGenerator()

# Database connection
def get_db_connection():
    database_url = os.environ.get('JAWSDB_URL') or os.environ.get('DATABASE_URL')
    if database_url:
        # Parse JawsDB MySQL URL: mysql://username:password@hostname:port/database
        parsed = urlparse(database_url)
        conn = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],  # Remove leading slash
            charset='utf8mb4',
            autocommit=True
        )
        return conn
    return None

# AWS S3 for file storage (Heroku addon)
def get_s3_client():
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')  
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    
    if aws_access_key and aws_secret_key:
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        return s3, bucket_name
    return None, None

@app.route('/')
def home():
    return jsonify({
        'service': 'EPUB to Audiobook Service',
        'status': 'running',
        'description': 'Convert EPUB files to audiobooks using Azure TTS',
        'endpoints': {
            'health': '/health',
            'process_epub': '/api/process-epub (POST)',
            'get_audiobooks': '/api/audiobooks/{user_id}',
            'stream_chapter': '/api/stream/{book_id}?chapter=1'
        },
        'version': '1.0.0',
        'documentation': 'https://github.com/your-repo/epub-audiobook-bot'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'epub-audiobook-cloud',
        'tts': 'azure' if not tts_service.use_edge_tts else 'edge',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process-epub', methods=['POST'])
def process_epub():
    """Process EPUB from Telegram bot"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        book_title = data.get('book_title', 'Unknown Book')
        epub_data = data.get('epub_data')  # Base64 encoded
        
        # Create processing job
        job_id = str(uuid.uuid4())
        
        # Start async processing
        asyncio.create_task(process_epub_async(job_id, user_id, book_title, epub_data))
        
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': f'Converting "{book_title}" to audiobook...',
            'estimated_time': '5-10 minutes'
        })
        
    except Exception as e:
        logger.error(f"EPUB processing error: {e}")
        return jsonify({'error': str(e)}), 500

async def process_epub_async(job_id: str, user_id: str, book_title: str, epub_data: str):
    """Async EPUB processing pipeline"""
    try:
        logger.info(f"Starting EPUB processing for job {job_id}")
        
        # 1. Extract chapters from EPUB
        chapters = extract_chapters_from_epub(epub_data)
        logger.info(f"Extracted {len(chapters)} chapters")
        
        # 2. Convert each chapter to MP3
        mp3_files = []
        for i, chapter in enumerate(chapters):
            logger.info(f"Converting chapter {i+1}/{len(chapters)}")
            
            # Create temp file for MP3
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                mp3_path = tmp_file.name
            
            # Convert to speech
            success = await tts_service.text_to_speech(
                chapter['text'], 
                mp3_path,
                voice_name="en-US-AriaNeural"
            )
            
            if success:
                # Upload to S3
                s3_url = upload_to_s3(mp3_path, f"{user_id}/{job_id}/chapter_{i+1}.mp3")
                if s3_url:
                    mp3_files.append({
                        'chapter': i + 1,
                        'title': chapter['title'],
                        'url': s3_url,
                        'duration': get_mp3_duration(mp3_path)
                    })
                
                # Cleanup temp file
                os.unlink(mp3_path)
        
        # 3. Save to database
        save_audiobook_to_db(user_id, job_id, book_title, mp3_files)
        
        # 4. Create podcast feed
        podcast_gen.add_audiobook_episode(user_id, book_title, mp3_files)
        
        logger.info(f"Successfully processed EPUB job {job_id}")
        
    except Exception as e:
        logger.error(f"Async processing failed for job {job_id}: {e}")

def extract_chapters_from_epub(epub_data: str) -> list:
    """Extract chapters from base64 EPUB data"""
    import base64
    import ebooklib
    from ebooklib import epub
    import re
    
    # Decode base64 EPUB data
    epub_bytes = base64.b64decode(epub_data)
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_file:
        tmp_file.write(epub_bytes)
        epub_path = tmp_file.name
    
    try:
        book = epub.read_epub(epub_path)
        chapters = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8')
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', content)
                text = text.strip()
                
                if text and len(text) > 100:
                    chapters.append({
                        'title': item.get_name() or f"Chapter {len(chapters) + 1}",
                        'text': text[:10000]  # Limit for demo
                    })
        
        return chapters
        
    finally:
        os.unlink(epub_path)

def upload_to_s3(file_path: str, s3_key: str) -> str:
    """Upload file to S3 and return URL"""
    try:
        s3, bucket_name = get_s3_client()
        if not s3 or not bucket_name:
            logger.warning("S3 not configured, skipping upload")
            return None
        
        s3.upload_file(file_path, bucket_name, s3_key)
        url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return url
        
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return None

def get_mp3_duration(file_path: str) -> int:
    """Get MP3 duration in seconds"""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(file_path)
        return len(audio) // 1000  # Convert to seconds
    except:
        return 0  # Default duration

def save_audiobook_to_db(user_id: str, book_id: str, title: str, mp3_files: list):
    """Save audiobook metadata to PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.warning("Database not available")
            return
        
        with conn.cursor() as cur:
            # Insert audiobook record
            cur.execute("""
                INSERT INTO audiobooks (id, user_id, title, chapters, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    chapters = VALUES(chapters)
            """, (book_id, user_id, title, len(mp3_files), datetime.now()))
            
            # Insert chapter records
            for mp3_file in mp3_files:
                cur.execute("""
                    INSERT INTO chapters (audiobook_id, chapter_number, title, url, duration)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        url = VALUES(url),
                        duration = VALUES(duration)
                """, (book_id, mp3_file['chapter'], mp3_file['title'], 
                     mp3_file['url'], mp3_file['duration']))
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Database save failed: {e}")

@app.route('/api/audiobooks/<user_id>')
def get_audiobooks(user_id):
    """Get user's audiobook library for Android Auto"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'audiobooks': [], 'total': 0})
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, chapters, created_at 
                FROM audiobooks 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            audiobooks = []
            for row in cur.fetchall():
                audiobooks.append({
                    'id': row[0],
                    'title': row[1],
                    'chapters': row[2],
                    'created_at': row[3].isoformat(),
                    'stream_url': f'/api/stream/{row[0]}'
                })
        
        conn.close()
        return jsonify({'audiobooks': audiobooks, 'total': len(audiobooks)})
        
    except Exception as e:
        logger.error(f"Get audiobooks failed: {e}")
        return jsonify({'audiobooks': [], 'total': 0})

@app.route('/api/stream/<book_id>')
def stream_audiobook(book_id):
    """Get streaming URLs for audiobook chapters"""
    try:
        chapter = request.args.get('chapter', '1')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 500
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT title, url, duration 
                FROM chapters 
                WHERE audiobook_id = %s AND chapter_number = %s
            """, (book_id, int(chapter)))
            
            row = cur.fetchone()
            if row:
                return jsonify({
                    'title': row[0],
                    'stream_url': row[1],
                    'duration': row[2],
                    'chapter': chapter
                })
            else:
                return jsonify({'error': 'Chapter not found'}), 404
        
    except Exception as e:
        logger.error(f"Stream request failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)