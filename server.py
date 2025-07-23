from flask import Flask, send_file, jsonify
import os
from pathlib import Path

app = Flask(__name__)

@app.route('/feed/<int:user_id>')
def serve_feed(user_id):
    """Serve RSS feed for user"""
    feed_path = Path(f"podcasts/{user_id}/feed.xml")
    if feed_path.exists():
        return send_file(feed_path, mimetype='application/rss+xml')
    return jsonify({'error': 'Feed not found'}), 404

@app.route('/audio/<int:user_id>/<book_title>/<filename>')
def serve_audio(user_id, book_title, filename):
    """Serve audio files"""
    audio_path = Path(f"podcasts/{user_id}/{book_title}/{filename}")
    if audio_path.exists():
        return send_file(audio_path, mimetype='audio/mpeg')
    return jsonify({'error': 'Audio file not found'}), 404

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Create podcasts directory if it doesn't exist
    Path("podcasts").mkdir(exist_ok=True)
    
    # Run server
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)