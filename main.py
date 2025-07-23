import os
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
from pathlib import Path
import tempfile
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import json

# Import our services
from azure_tts import AzureTTSService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
tts_service = AzureTTSService()

# Cloudflare R2 storage
def get_r2_client():
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

@app.route('/')
def home():
    return jsonify({
        'service': 'EPUB to Audiobook Service',
        'status': 'running',
        'description': 'Convert EPUB files to audiobooks using Azure TTS',
        'storage': 'Cloudflare R2',
        'endpoints': {
            'health': '/health',
            'process_epub': '/api/process-epub (POST)',
            'list_audiobooks': '/api/audiobooks/{user_id}',
            'download_audiobook': '/api/download/{audiobook_id}'
        },
        'version': '2.0.0 - Simplified R2 Storage'
    })

@app.route('/health')
def health():
    r2, bucket = get_r2_client()
    storage_status = 'connected' if r2 else 'not_configured'
    
    return jsonify({
        'status': 'healthy',
        'service': 'epub-audiobook-cloud',
        'tts': 'azure' if not tts_service.use_edge_tts else 'edge',
        'storage': f'cloudflare_r2_{storage_status}',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process-epub', methods=['POST'])
def process_epub():
    """Process EPUB from Telegram bot and store in R2"""
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
            'storage': 'cloudflare_r2',
            'estimated_time': '5-10 minutes'
        })
        
    except Exception as e:
        logger.error(f"EPUB processing error: {e}")
        return jsonify({'error': str(e)}), 500

async def process_epub_async(job_id: str, user_id: str, book_title: str, epub_data: str):
    """Simplified EPUB processing - just convert and store in R2"""
    try:
        logger.info(f"Starting EPUB processing for job {job_id}")
        
        # 1. Extract chapters from EPUB
        chapters = extract_chapters_from_epub(epub_data)
        logger.info(f"Extracted {len(chapters)} chapters")
        
        audiobook_metadata = {
            'job_id': job_id,
            'user_id': user_id,
            'book_title': book_title,
            'chapters': [],
            'created_at': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        # 2. Convert each chapter to MP3 and upload to R2
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
                # Upload to R2
                r2_key = f"{user_id}/{job_id}/chapter_{i+1}.mp3"
                r2_url = upload_to_r2(mp3_path, r2_key)
                
                if r2_url:
                    audiobook_metadata['chapters'].append({
                        'chapter': i + 1,
                        'title': chapter['title'],
                        'url': r2_url,
                        'r2_key': r2_key,
                        'duration': get_mp3_duration(mp3_path)
                    })
                
                # Cleanup temp file
                os.unlink(mp3_path)
        
        # 3. Save audiobook metadata to R2 as JSON
        metadata_key = f"{user_id}/{job_id}/metadata.json"
        save_metadata_to_r2(audiobook_metadata, metadata_key)
        
        logger.info(f"Successfully processed EPUB job {job_id} - {len(audiobook_metadata['chapters'])} chapters stored in R2")
        
    except Exception as e:
        logger.error(f"Async processing failed for job {job_id}: {e}")

def upload_to_r2(file_path: str, r2_key: str) -> str:
    """Upload file to Cloudflare R2 and return URL"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            logger.warning("R2 not configured, skipping upload")
            return None
        
        r2.upload_file(file_path, bucket_name, r2_key)
        # Cloudflare R2 public URL format
        url = f"https://pub-{bucket_name}.r2.dev/{r2_key}"
        return url
        
    except Exception as e:
        logger.error(f"R2 upload failed: {e}")
        return None

def save_metadata_to_r2(metadata: dict, r2_key: str):
    """Save audiobook metadata as JSON to R2"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return
        
        # Upload JSON metadata
        r2.put_object(
            Bucket=bucket_name,
            Key=r2_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Saved metadata to R2: {r2_key}")
        
    except Exception as e:
        logger.error(f"Failed to save metadata to R2: {e}")

@app.route('/api/audiobooks/<user_id>')
def get_audiobooks(user_id):
    """Get user's audiobook library from R2"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return jsonify({'audiobooks': [], 'total': 0})
        
        # List user's audiobooks in R2
        prefix = f"{user_id}/"
        response = r2.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
        
        audiobooks = []
        for obj in response.get('CommonPrefixes', []):
            # Each folder is a job_id (audiobook)
            job_folder = obj['Prefix']
            metadata_key = f"{job_folder}metadata.json"
            
            try:
                # Get metadata
                metadata_obj = r2.get_object(Bucket=bucket_name, Key=metadata_key)
                metadata = json.loads(metadata_obj['Body'].read())
                
                audiobooks.append({
                    'id': metadata['job_id'],
                    'title': metadata['book_title'],
                    'chapters': len(metadata['chapters']),
                    'created_at': metadata['created_at'],
                    'download_url': f'/api/download/{metadata["job_id"]}'
                })
            except Exception as e:
                logger.warning(f"Could not load metadata for {metadata_key}: {e}")
        
        return jsonify({'audiobooks': audiobooks, 'total': len(audiobooks)})
        
    except Exception as e:
        logger.error(f"Get audiobooks failed: {e}")
        return jsonify({'audiobooks': [], 'total': 0})

@app.route('/api/download/<audiobook_id>')
def download_audiobook(audiobook_id):
    """Get download URLs for all chapters of an audiobook"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return jsonify({'error': 'Storage not available'}), 500
        
        # Find the audiobook metadata
        # We need to scan user folders since we don't store user_id in the route
        response = r2.list_objects_v2(Bucket=bucket_name, Prefix="", Delimiter='/')
        
        for prefix_obj in response.get('CommonPrefixes', []):
            user_folder = prefix_obj['Prefix']
            metadata_key = f"{user_folder}{audiobook_id}/metadata.json"
            
            try:
                metadata_obj = r2.get_object(Bucket=bucket_name, Key=metadata_key)
                metadata = json.loads(metadata_obj['Body'].read())
                
                return jsonify({
                    'audiobook_id': audiobook_id,
                    'title': metadata['book_title'],
                    'chapters': metadata['chapters'],
                    'total_chapters': len(metadata['chapters'])
                })
            except:
                continue
        
        return jsonify({'error': 'Audiobook not found'}), 404
        
    except Exception as e:
        logger.error(f"Download request failed: {e}")
        return jsonify({'error': str(e)}), 500

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