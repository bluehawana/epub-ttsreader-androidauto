import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin

class PodcastGenerator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.podcast_dir = Path("podcasts")
        self.podcast_dir.mkdir(exist_ok=True)
        self.user_feeds = {}
    
    def create_user_feed(self, user_id: int, user_name: str = None) -> str:
        """Create or get existing podcast feed for a user"""
        if user_id in self.user_feeds:
            return self.user_feeds[user_id]['feed_url']
        
        # Create feed directory
        user_dir = self.podcast_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        
        # Initialize feed
        fg = FeedGenerator()
        fg.id(f"{self.base_url}/feed/{user_id}")
        fg.title(f"{user_name or f'User {user_id}'}'s Audiobooks")
        fg.link(href=f"{self.base_url}/feed/{user_id}", rel='alternate')
        fg.description(f"Personal audiobook collection for {user_name or f'User {user_id}'}")
        fg.author({'name': 'EPUB Audiobook Bot', 'email': 'bot@example.com'})
        fg.language('en')
        fg.image(url=f"{self.base_url}/static/podcast-icon.png", 
                 title="Audiobook Podcast", 
                 link=f"{self.base_url}/feed/{user_id}")
        
        # Save feed info
        self.user_feeds[user_id] = {
            'feed_generator': fg,
            'feed_url': f"{self.base_url}/feed/{user_id}",
            'user_dir': user_dir,
            'episodes': []
        }
        
        # Generate initial RSS file
        self._save_feed(user_id)
        
        return self.user_feeds[user_id]['feed_url']
    
    def add_audiobook_episode(self, user_id: int, book_title: str, 
                            audio_files: List[Dict], book_metadata: Dict = None):
        """Add a complete audiobook as podcast episodes"""
        if user_id not in self.user_feeds:
            self.create_user_feed(user_id)
        
        fg = self.user_feeds[user_id]['feed_generator']
        user_dir = self.user_feeds[user_id]['user_dir']
        
        # Create book directory
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        book_dir = user_dir / safe_title
        book_dir.mkdir(exist_ok=True)
        
        # Copy audio files to podcast directory and create episodes
        for i, audio_file in enumerate(audio_files):
            try:
                # Copy audio file
                chapter_filename = f"{safe_title}_chapter_{i+1}.mp3"
                dest_path = book_dir / chapter_filename
                
                # Copy file (in real implementation, you'd move from temp)
                import shutil
                shutil.copy2(audio_file['path'], dest_path)
                
                # Create episode
                fe = fg.add_entry()
                episode_id = f"{user_id}_{safe_title}_{i+1}_{int(datetime.now().timestamp())}"
                
                fe.id(episode_id)
                fe.title(f"{book_title} - {audio_file['title']}")
                fe.description(f"Chapter {i+1} of {book_title}")
                fe.published(datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))
                
                # Audio enclosure
                audio_url = f"{self.base_url}/audio/{user_id}/{safe_title}/{chapter_filename}"
                fe.enclosure(audio_url, str(dest_path.stat().st_size), 'audio/mpeg')
                
                # Store episode info
                self.user_feeds[user_id]['episodes'].append({
                    'title': f"{book_title} - Chapter {i+1}",
                    'file_path': dest_path,
                    'url': audio_url,
                    'book': book_title
                })
                
            except Exception as e:
                print(f"Error adding episode {i+1}: {e}")
        
        # Save updated feed
        self._save_feed(user_id)
        
        return len(audio_files)  # Return number of episodes added
    
    def _save_feed(self, user_id: int):
        """Save RSS feed to file"""
        if user_id not in self.user_feeds:
            return
        
        fg = self.user_feeds[user_id]['feed_generator']
        user_dir = self.user_feeds[user_id]['user_dir']
        
        # Save RSS file
        rss_path = user_dir / "feed.xml"
        fg.rss_file(str(rss_path))
        
        # Save metadata
        metadata_path = user_dir / "metadata.json"
        metadata = {
            'user_id': user_id,
            'feed_url': self.user_feeds[user_id]['feed_url'],
            'episodes': [
                {
                    'title': ep['title'],
                    'url': ep['url'],
                    'book': ep['book']
                }
                for ep in self.user_feeds[user_id]['episodes']
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_feed_url(self, user_id: int) -> str:
        """Get podcast feed URL for user"""
        if user_id in self.user_feeds:
            return self.user_feeds[user_id]['feed_url']
        return None
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user's podcast statistics"""
        if user_id not in self.user_feeds:
            return {'episodes': 0, 'books': 0}
        
        episodes = self.user_feeds[user_id]['episodes']
        books = set(ep['book'] for ep in episodes)
        
        return {
            'episodes': len(episodes),
            'books': len(books),
            'latest_book': episodes[-1]['book'] if episodes else None
        }