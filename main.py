import os
import logging
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from pathlib import Path
import tempfile
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import json
import threading
import time
import base64
import secrets
import qrcode
from io import BytesIO

# Import our services
from edge_tts_service import EdgeTTSService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
tts_service = EdgeTTSService()

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
        'description': 'Convert EPUB files to audiobooks using EdgeTTS',
        'storage': 'Cloudflare R2',
        'endpoints': {
            'health': '/health',
            'process_epub': '/api/process-epub (POST)',
            'process_all_epubs': '/api/process-all-epubs (POST)',
            'list_audiobooks': '/api/audiobooks/{user_id}',
            'download_audiobook': '/api/download/{audiobook_id}',
            'job_status': '/api/job-status/{job_id}',
            'processing_status': '/api/processing-status',
            'generate_auth_qr': '/api/generate-auth-qr/{user_id}',
            'verify_auth_token': '/api/verify-auth-token/{token}'
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
        'tts': 'edge',
        'storage': f'cloudflare_r2_{storage_status}',
        'r2_scanner': 'active',
        'processed_epubs': len(processed_epubs),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/job-status/<job_id>')
def get_job_status(job_id):
    """Get processing status for a specific job"""
    try:
        if job_id in processing_jobs:
            return jsonify(processing_jobs[job_id])
        
        # Check if job is completed by looking for metadata in R2
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return jsonify({'error': 'Storage not available'}), 500
        
        # Search for metadata across all user folders
        response = r2.list_objects_v2(Bucket=bucket_name, Prefix="")
        
        for obj in response.get('Contents', []):
            if f'/{job_id}/metadata.json' in obj['Key']:
                try:
                    metadata_obj = r2.get_object(Bucket=bucket_name, Key=obj['Key'])
                    metadata = json.loads(metadata_obj['Body'].read())
                    
                    return jsonify({
                        'job_id': job_id,
                        'status': 'completed',
                        'progress': 100,
                        'book_title': metadata.get('book_title', 'Unknown'),
                        'chapters': len(metadata.get('chapters', [])),
                        'completed_at': metadata.get('created_at'),
                        'message': f'Audiobook ready with {len(metadata.get("chapters", []))} chapters'
                    })
                except Exception as e:
                    logger.error(f"Error reading metadata for job {job_id}: {e}")
        
        # Job not found
        return jsonify({
            'job_id': job_id,
            'status': 'not_found',
            'message': 'Job not found or expired'
        }), 404
        
    except Exception as e:
        logger.error(f"Job status check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing-status')
def get_processing_status():
    """Get status of all currently processing jobs"""
    try:
        active_jobs = []
        completed_count = 0
        
        for job_id, job_info in processing_jobs.items():
            if job_info['status'] == 'processing':
                active_jobs.append(job_info)
            elif job_info['status'] == 'completed':
                completed_count += 1
        
        return jsonify({
            'active_jobs': active_jobs,
            'total_active': len(active_jobs),
            'total_completed': completed_count,
            'processed_epubs': len(processed_epubs),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Processing status check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-bucket')
def list_bucket():
    """List all files in R2 bucket for debugging"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return jsonify({'error': 'R2 not configured'}), 500
        
        response = r2.list_objects_v2(Bucket=bucket_name, Prefix="")
        files = []
        
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'modified': obj['LastModified'].isoformat()
            })
        
        return jsonify({
            'bucket': bucket_name,
            'total_files': len(files),
            'files': files[:50]  # Limit to first 50 files
        })
        
    except Exception as e:
        logger.error(f"List bucket error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/<user_id>/<job_id>/<chapter_file>')
def stream_audio(user_id, job_id, chapter_file):
    """Stream audio file through Flask proxy from R2 with range support"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return jsonify({'error': 'R2 not configured'}), 500
        
        r2_key = f"{user_id}/{job_id}/{chapter_file}"
        
        # Get file metadata first
        try:
            head_response = r2.head_object(Bucket=bucket_name, Key=r2_key)
            file_size = head_response['ContentLength']
        except Exception as e:
            logger.error(f"File not found in R2: {r2_key}")
            return jsonify({'error': 'File not found'}), 404
        
        # Handle range requests for better streaming
        range_header = request.headers.get('Range')
        if range_header:
            # Parse range header: bytes=start-end
            range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                # Ensure end doesn't exceed file size
                end = min(end, file_size - 1)
                
                try:
                    # Get partial content from R2
                    range_str = f"bytes={start}-{end}"
                    response = r2.get_object(Bucket=bucket_name, Key=r2_key, Range=range_str)
                    audio_data = response['Body'].read()
                    
                    from flask import Response
                    return Response(
                        audio_data,
                        206,  # Partial Content
                        headers={
                            'Content-Type': 'audio/mpeg',
                            'Accept-Ranges': 'bytes',
                            'Content-Range': f'bytes {start}-{end}/{file_size}',
                            'Content-Length': str(len(audio_data)),
                            'Cache-Control': 'public, max-age=3600',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Headers': 'Range'
                        }
                    )
                except Exception as range_error:
                    logger.warning(f"Range request failed, falling back to full file: {range_error}")
                    # Fall through to full file download
        
        # Get full file from R2
        response = r2.get_object(Bucket=bucket_name, Key=r2_key)
        audio_data = response['Body'].read()
        
        # Return audio file with proper headers
        from flask import Response
        return Response(
            audio_data,
            mimetype='audio/mpeg',
            headers={
                'Content-Disposition': f'inline; filename="{chapter_file}"',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(len(audio_data)),
                'Cache-Control': 'public, max-age=3600',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Range'
            }
        )
        
    except Exception as e:
        logger.error(f"Stream audio error: {e}")
        return jsonify({'error': str(e)}), 404

@app.route('/api/process-all-epubs', methods=['POST'])
def process_all_epubs():
    """Manually trigger processing of all EPUBs in bucket"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return jsonify({'error': 'R2 not configured'}), 500
        
        # Find all EPUB files
        response = r2.list_objects_v2(Bucket=bucket_name, Prefix="")
        epub_files = []
        
        for obj in response.get('Contents', []):
            key = obj['Key']
            if '/epubs/' in key and key.endswith('.epub'):
                epub_files.append(key)
        
        # Process each EPUB
        for epub_key in epub_files:
            if epub_key not in processed_epubs:
                logger.info(f"🔄 Manually processing EPUB: {epub_key}")
                process_epub_from_r2(epub_key)
                processed_epubs.add(epub_key)
        
        return jsonify({
            'message': f'Processing {len(epub_files)} EPUB files',
            'epub_files': epub_files,
            'already_processed': len([f for f in epub_files if f in processed_epubs])
        })
        
    except Exception as e:
        logger.error(f"Manual processing error: {e}")
        return jsonify({'error': str(e)}), 500

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
        
        # Track job status
        processing_jobs[job_id] = {
            'job_id': job_id,
            'user_id': user_id,
            'book_title': book_title,
            'status': 'processing',
            'progress': 0,
            'started_at': datetime.now().isoformat(),
            'message': 'Starting EPUB processing...'
        }
        
        # Start async processing
        threading.Thread(
            target=lambda: asyncio.run(process_epub_async(job_id, user_id, book_title, epub_data)),
            daemon=True
        ).start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': f'Converting "{book_title}" to audiobook...',
            'storage': 'cloudflare_r2',
            'estimated_time': '5-10 minutes',
            'status_url': f'/api/job-status/{job_id}'
        })
        
    except Exception as e:
        logger.error(f"EPUB processing error: {e}")
        return jsonify({'error': str(e)}), 500

async def process_epub_async(job_id: str, user_id: str, book_title: str, epub_data: str):
    """Simplified EPUB processing - just convert and store in R2"""
    try:
        logger.info(f"Starting EPUB processing for job {job_id}")
        
        # Update job status
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'status': 'processing',
                'progress': 5,
                'message': 'Extracting chapters from EPUB...'
            })
        
        # 1. Extract chapters from EPUB
        chapters = extract_chapters_from_epub(epub_data)
        logger.info(f"Extracted {len(chapters)} chapters")
        
        # Update job status
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'progress': 10,
                'message': f'Found {len(chapters)} chapters, starting TTS conversion...',
                'total_chapters': len(chapters)
            })
        
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
            
            # Update progress
            progress = 10 + (i * 80 // len(chapters))  # 10-90% for TTS processing
            if job_id in processing_jobs:
                processing_jobs[job_id].update({
                    'progress': progress,
                    'message': f'Converting chapter {i+1}/{len(chapters)} to speech...',
                    'current_chapter': i + 1
                })
            
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
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'progress': 95,
                'message': 'Saving audiobook metadata...'
            })
        
        metadata_key = f"{user_id}/{job_id}/metadata.json"
        save_metadata_to_r2(audiobook_metadata, metadata_key)
        
        # Mark job as completed
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': f'Audiobook ready! {len(audiobook_metadata["chapters"])} chapters processed.',
                'completed_at': datetime.now().isoformat(),
                'chapters_processed': len(audiobook_metadata['chapters'])
            })
        
        logger.info(f"Successfully processed EPUB job {job_id} - {len(audiobook_metadata['chapters'])} chapters stored in R2")
        
    except Exception as e:
        logger.error(f"Async processing failed for job {job_id}: {e}")
        
        # Mark job as failed
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': f'Processing failed: {str(e)}',
                'failed_at': datetime.now().isoformat(),
                'error': str(e)
            })

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

def get_mp3_duration(file_path: str) -> int:
    """Get MP3 duration in seconds"""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(file_path)
        return len(audio) // 1000  # Convert to seconds
    except:
        return 0  # Default duration

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
                
                # Update chapter URLs to use Flask streaming proxy
                updated_chapters = []
                for chapter in metadata['chapters']:
                    updated_chapter = chapter.copy()
                    # Replace R2 URL with Flask streaming URL
                    r2_key = updated_chapter['r2_key']
                    user_id, job_id, filename = r2_key.split('/')
                    updated_chapter['url'] = f"https://epub-audiobook-service-ab00bb696e09.herokuapp.com/api/stream/{user_id}/{job_id}/{filename}"
                    updated_chapters.append(updated_chapter)
                
                return jsonify({
                    'audiobook_id': audiobook_id,
                    'title': metadata['book_title'],
                    'chapters': updated_chapters,
                    'total_chapters': len(updated_chapters)
                })
            except:
                continue
        
        return jsonify({'error': 'Audiobook not found'}), 404
        
    except Exception as e:
        logger.error(f"Download request failed: {e}")
        return jsonify({'error': str(e)}), 500

# QR Code Authentication System
auth_tokens = {}  # Store temporary auth tokens: {token: {user_id, created_at, expires_at}}

@app.route('/api/generate-auth-qr/<user_id>')
def generate_auth_qr(user_id):
    """Generate QR code for authentication"""
    try:
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Store token with expiration (5 minutes)
        from datetime import datetime, timedelta
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=5)
        
        auth_tokens[token] = {
            'user_id': user_id,
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        # Create QR code content (URL that app will scan)
        base_url = request.host_url.rstrip('/')
        qr_content = f"{base_url}/auth?token={token}&user_id={user_id}"
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for JSON response
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        logger.info(f"Generated QR code for user {user_id}, token expires at {expires_at}")
        
        return jsonify({
            'token': token,
            'user_id': user_id,
            'qr_code_base64': qr_base64,
            'qr_content': qr_content,
            'expires_at': expires_at.isoformat(),
            'expires_in_minutes': 5
        })
        
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-auth-token/<token>')
def verify_auth_token(token):
    """Verify authentication token and return user_id"""
    try:
        # Check if token exists
        if token not in auth_tokens:
            return jsonify({
                'valid': False,
                'error': 'Invalid token'
            }), 400
        
        # Check if token is expired
        token_data = auth_tokens[token]
        from datetime import datetime
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        
        if datetime.now() > expires_at:
            # Clean up expired token
            del auth_tokens[token]
            return jsonify({
                'valid': False,
                'error': 'Token expired'
            }), 400
        
        # Token is valid
        user_id = token_data['user_id']
        
        # Optionally, clean up used token (one-time use)
        del auth_tokens[token]
        
        logger.info(f"Successfully authenticated user {user_id} with token")
        
        return jsonify({
            'valid': True,
            'user_id': user_id,
            'authenticated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth')
def auth_redirect():
    """Handle QR code scan redirect (for web browsers)"""
    token = request.args.get('token')
    user_id = request.args.get('user_id')
    
    if token and user_id:
        # This endpoint could show a web page confirming authentication
        # For now, just return JSON
        return jsonify({
            'message': 'QR Code scanned successfully!',
            'token': token,
            'user_id': user_id,
            'instructions': 'Your mobile app should now be authenticated.'
        })
    else:
        return jsonify({'error': 'Invalid QR code'}), 400

# Cleanup expired tokens periodically
def cleanup_expired_tokens():
    """Remove expired authentication tokens"""
    from datetime import datetime
    current_time = datetime.now()
    
    expired_tokens = []
    for token, data in auth_tokens.items():
        expires_at = datetime.fromisoformat(data['expires_at'])
        if current_time > expires_at:
            expired_tokens.append(token)
    
    for token in expired_tokens:
        del auth_tokens[token]
        
    if expired_tokens:
        logger.info(f"Cleaned up {len(expired_tokens)} expired auth tokens")

# R2 EPUB Scanner - Background Process
processed_epubs = set()  # Track processed files
processing_jobs = {}  # Track active processing jobs

def scan_r2_for_epubs():
    """Background thread to scan R2 for new EPUB files and process them"""
    logger.info("🔍 Starting R2 EPUB scanner...")
    
    while True:
        try:
            r2, bucket_name = get_r2_client()
            if not r2 or not bucket_name:
                logger.warning("R2 not configured for scanning")
                time.sleep(60)
                continue
            
            # Scan for EPUB files in user folders
            response = r2.list_objects_v2(Bucket=bucket_name, Prefix="")
            
            for obj in response.get('Contents', []):
                key = obj['Key']
                
                # Look for EPUB files in epubs/ folders
                if '/epubs/' in key and key.endswith('.epub'):
                    if key not in processed_epubs:
                        logger.info(f"📚 Found new EPUB: {key}")
                        process_epub_from_r2(key)
                        processed_epubs.add(key)
            
            # Sleep for 30 seconds before next scan
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"R2 scanning error: {e}")
            time.sleep(60)

def process_epub_from_r2(r2_key: str):
    """Process EPUB file from R2 storage"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return
        
        # Extract user_id and filename from key: user_id/epubs/filename.epub
        parts = r2_key.split('/')
        if len(parts) >= 3:
            user_id = parts[0]
            filename = parts[-1]
            book_title = filename.replace('.epub', '')
            
            logger.info(f"📖 Processing EPUB: {book_title} for user {user_id}")
            
            # Download EPUB from R2
            epub_data = download_epub_from_r2(r2_key)
            if epub_data:
                # Generate job ID
                job_id = str(uuid.uuid4())
                
                # Start async processing
                threading.Thread(
                    target=lambda: asyncio.run(process_epub_async(job_id, user_id, book_title, epub_data)),
                    daemon=True
                ).start()
                logger.info(f"🎧 Started TTS conversion job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing EPUB from R2 {r2_key}: {e}")

def download_epub_from_r2(r2_key: str) -> str:
    """Download EPUB file from R2 and return as base64"""
    try:
        r2, bucket_name = get_r2_client()
        if not r2 or not bucket_name:
            return None
        
        # Download file
        response = r2.get_object(Bucket=bucket_name, Key=r2_key)
        epub_bytes = response['Body'].read()
        
        # Convert to base64
        epub_b64 = base64.b64encode(epub_bytes).decode('utf-8')
        logger.info(f"📥 Downloaded EPUB from R2: {r2_key}")
        return epub_b64
        
    except Exception as e:
        logger.error(f"Error downloading EPUB from R2 {r2_key}: {e}")
        return None

# Start background scanner thread
def start_r2_scanner():
    """Start the R2 scanner in a background thread"""
    scanner_thread = threading.Thread(target=scan_r2_for_epubs, daemon=True)
    scanner_thread.start()
    logger.info("🚀 R2 EPUB scanner started!")

if __name__ == '__main__':
    # Start R2 scanner
    start_r2_scanner()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)