#!/usr/bin/env python3
"""
Check EPUBs and audiobooks in R2 storage to see processing status
"""
import boto3
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

def get_r2_client():
    """Get Cloudflare R2 client"""
    r2_endpoint = os.environ.get('R2_ENDPOINT_URL')
    r2_access_key = os.environ.get('R2_ACCESS_KEY_ID')
    r2_secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
    
    if r2_endpoint and r2_access_key and r2_secret_key:
        r2 = boto3.client(
            's3',
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            region_name='auto'
        )
        return r2
    return None

def format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {size_names[i]}"

def main():
    r2 = get_r2_client()
    if not r2:
        print("❌ R2 client not configured")
        return
    
    bucket_name = "ebuppool"  # Using the existing bucket name
    
    try:
        print(f"📂 Checking contents of bucket '{bucket_name}'...")
        print("=" * 80)
        
        # List all objects in the bucket
        response = r2.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response:
            print("📭 Bucket is empty")
            return
        
        objects = response['Contents']
        print(f"📊 Found {len(objects)} objects in bucket")
        print()
        
        # Categorize files
        epubs = []
        audiobooks = []
        user_dirs = {}
        other_files = []
        
        for obj in objects:
            key = obj['Key']
            size = obj['Size']
            modified = obj['LastModified']
            
            if key.endswith('.epub'):
                epubs.append({
                    'key': key,
                    'size': size,
                    'modified': modified
                })
            elif '/audiobooks/' in key or key.endswith('.mp3') or key.endswith('.wav'):
                audiobooks.append({
                    'key': key,
                    'size': size,
                    'modified': modified
                })
            elif key.startswith('user_'):
                user_id = key.split('/')[0] if '/' in key else key.split('_')[1] if '_' in key else 'unknown'
                if user_id not in user_dirs:
                    user_dirs[user_id] = []
                user_dirs[user_id].append({
                    'key': key,
                    'size': size,
                    'modified': modified
                })
            else:
                other_files.append({
                    'key': key,
                    'size': size,
                    'modified': modified
                })
        
        # Display EPUBs
        if epubs:
            print("📚 EPUB Files:")
            print("-" * 60)
            for epub in epubs:
                print(f"  📖 {epub['key']}")
                print(f"     Size: {format_size(epub['size'])}")
                print(f"     Modified: {epub['modified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print()
        
        # Display audiobooks
        if audiobooks:
            print("🎧 Audiobook Files:")
            print("-" * 60)
            for audio in audiobooks:
                print(f"  🔊 {audio['key']}")
                print(f"     Size: {format_size(audio['size'])}")
                print(f"     Modified: {audio['modified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print()
        
        # Display user directories
        if user_dirs:
            print("👤 User Directories:")
            print("-" * 60)
            for user_id, files in user_dirs.items():
                print(f"  👤 User: {user_id}")
                for file in files:
                    print(f"    📄 {file['key']}")
                    print(f"       Size: {format_size(file['size'])}")
                    print(f"       Modified: {file['modified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print()
        
        # Display other files
        if other_files:
            print("📄 Other Files:")
            print("-" * 60)
            for file in other_files:
                print(f"  📄 {file['key']}")
                print(f"     Size: {format_size(file['size'])}")
                print(f"     Modified: {file['modified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print()
        
        # Summary
        print("📊 SUMMARY:")
        print("=" * 40)
        print(f"📚 EPUBs: {len(epubs)}")
        print(f"🎧 Audiobooks: {len(audiobooks)}")
        print(f"👤 User directories: {len(user_dirs)}")
        print(f"📄 Other files: {len(other_files)}")
        print(f"📦 Total objects: {len(objects)}")
        
        # Check for TTS processing
        if epubs and not audiobooks:
            print("\n⚠️  WARNING: Found EPUBs but no audiobook files!")
            print("   This suggests TTS processing may not have completed or failed.")
        elif epubs and audiobooks:
            print("\n✅ Found both EPUBs and audiobooks - TTS processing appears to be working!")
        
    except Exception as e:
        print(f"❌ Error accessing bucket: {e}")

if __name__ == '__main__':
    main()