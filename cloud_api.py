from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from pathlib import Path
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory storage (use database in production)
users_library = {}
processing_queue = {}

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'audiobook-cloud'})

@app.route('/api/process-epub', methods=['POST'])
def process_epub():
    """Process EPUB file from Telegram bot"""
    try:
        user_id = request.json.get('user_id')
        epub_data = request.json.get('epub_data')  # Base64 encoded
        book_title = request.json.get('book_title', 'Unknown Book')
        
        # Generate processing job
        job_id = str(uuid.uuid4())
        processing_queue[job_id] = {
            'user_id': user_id,
            'book_title': book_title,
            'status': 'processing',
            'created_at': datetime.now().isoformat()
        }
        
        # TODO: Actual EPUB processing (async)
        # For now, simulate processing
        
        return jsonify({
            'job_id': job_id,
            'status': 'accepted',
            'message': f'Processing "{book_title}"...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audiobooks/<user_id>')
def get_audiobooks(user_id):
    """Get user's audiobook library for Android Auto"""
    try:
        user_books = users_library.get(user_id, [])
        
        # Format for Android Auto
        audiobooks = []
        for book in user_books:
            audiobooks.append({
                'id': book['id'],
                'title': book['title'],
                'author': book.get('author', 'Unknown'),
                'chapters': len(book.get('chapters', [])),
                'duration': book.get('total_duration', '0:00'),
                'cover_url': book.get('cover_url'),
                'stream_url': f"/api/stream/{book['id']}"
            })
        
        return jsonify({
            'audiobooks': audiobooks,
            'total': len(audiobooks),
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/<book_id>')
def stream_audiobook(book_id):
    """Stream audiobook chapters for Android Auto"""
    try:
        chapter = request.args.get('chapter', '1')
        
        # TODO: Find actual MP3 file and stream it
        # For demo, return mock response
        
        return jsonify({
            'book_id': book_id,
            'chapter': chapter,
            'stream_url': f'https://cdn.example.com/audiobooks/{book_id}/chapter_{chapter}.mp3',
            'duration': 1800,  # 30 minutes
            'title': f'Chapter {chapter}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/<user_id>')
def sync_updates(user_id):
    """Check for new audiobooks (Android Auto polling)"""
    try:
        user_books = users_library.get(user_id, [])
        last_sync = request.args.get('last_sync')
        
        # Check for new books since last sync
        new_books = []
        if last_sync:
            # Filter books newer than last_sync
            pass
        
        return jsonify({
            'new_books': len(new_books),
            'books': new_books,
            'sync_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Authenticate Android Auto app"""
    try:
        user_id = request.json.get('user_id')
        auth_token = request.json.get('auth_token')
        
        # TODO: Validate auth token from Telegram bot
        
        return jsonify({
            'authenticated': True,
            'user_id': user_id,
            'message': 'Android Auto linked successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Demo endpoint - add sample book
@app.route('/api/demo/add-book/<user_id>')
def add_demo_book(user_id):
    """Add demo book for testing"""
    if user_id not in users_library:
        users_library[user_id] = []
    
    demo_book = {
        'id': str(uuid.uuid4()),
        'title': 'Demo Audiobook',
        'author': 'Test Author',
        'chapters': [
            {'id': '1', 'title': 'Chapter 1', 'duration': '25:30'},
            {'id': '2', 'title': 'Chapter 2', 'duration': '32:15'},
            {'id': '3', 'title': 'Chapter 3', 'duration': '28:45'}
        ],
        'total_duration': '1:26:30',
        'created_at': datetime.now().isoformat()
    }
    
    users_library[user_id].append(demo_book)
    
    return jsonify({
        'message': 'Demo book added!',
        'book': demo_book
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)