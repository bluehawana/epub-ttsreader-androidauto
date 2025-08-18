#!/usr/bin/env python3
"""
Simple R2 Storage Analyzer
Lists contents of your R2 bucket to understand the structure
"""

import os
import json
import boto3
from collections import defaultdict
from datetime import datetime

# Don't load .env files as they contain template values

def get_r2_client():
    """Initialize R2 client"""
    # Get R2 credentials from environment variables
    r2_endpoint = os.environ.get('R2_ENDPOINT_URL')
    r2_access_key = os.environ.get('R2_ACCESS_KEY_ID')
    r2_secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
    r2_bucket = os.environ.get('R2_BUCKET_NAME', 'ebuppool')
    
    if not all([r2_endpoint, r2_access_key, r2_secret_key]):
        print("❌ R2 credentials not found in environment variables")
        print("Set these environment variables:")
        print("  export R2_ENDPOINT_URL='https://your-account-id.r2.cloudflarestorage.com'")
        print("  export R2_ACCESS_KEY_ID='your_access_key'")
        print("  export R2_SECRET_ACCESS_KEY='your_secret_key'")
        print("  export R2_BUCKET_NAME='ebuppool'")
        return None, None
    
    r2 = boto3.client(
        's3',
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
        region_name='auto'
    )
    
    return r2, r2_bucket

def list_bucket_contents(r2, bucket_name, max_objects=100):
    """List bucket contents with analysis"""
    print(f"🪣 Listing contents of bucket: {bucket_name}")
    print("="*80)
    
    try:
        response = r2.list_objects_v2(Bucket=bucket_name, MaxKeys=max_objects)
        objects = response.get('Contents', [])
        
        if not objects:
            print("📭 Bucket is empty or no access")
            return
        
        print(f"📊 Showing first {len(objects)} objects (total may be more)")
        print()
        
        # Group by user and analyze structure
        users = defaultdict(lambda: {'folders': set(), 'files': []})
        audiobooks = defaultdict(list)
        
        for obj in objects:
            key = obj['Key']
            size = obj['Size']
            modified = obj['LastModified']
            
            parts = key.split('/')
            if len(parts) >= 2:
                user_id = parts[0]
                folder = parts[1] if len(parts) > 2 else 'root'
                
                users[user_id]['folders'].add(folder)
                users[user_id]['files'].append({
                    'key': key,
                    'size': size,
                    'modified': modified
                })
                
                # Check if it's an audiobook metadata
                if key.endswith('metadata.json'):
                    try:
                        metadata_obj = r2.get_object(Bucket=bucket_name, Key=key)
                        metadata = json.loads(metadata_obj['Body'].read())
                        book_title = metadata.get('book_title', 'Unknown')
                        job_id = parts[1] if len(parts) > 1 else 'unknown'
                        
                        audiobooks[book_title].append({
                            'user_id': user_id,
                            'job_id': job_id,
                            'key': key,
                            'modified': modified,
                            'chapters': len(metadata.get('chapters', []))
                        })
                    except Exception as e:
                        print(f"⚠️  Could not read metadata {key}: {e}")
        
        # Print user analysis
        for user_id, data in users.items():
            total_size = sum(f['size'] for f in data['files'])
            print(f"👤 User: {user_id}")
            print(f"   📁 Folders: {', '.join(sorted(data['folders']))}")
            print(f"   📄 Files: {len(data['files'])} ({total_size / 1024 / 1024:.1f} MB)")
            
            # Show some example files
            for file_info in data['files'][:5]:
                print(f"      📄 {file_info['key']} ({file_info['size'] / 1024:.1f} KB)")
            
            if len(data['files']) > 5:
                print(f"      ... and {len(data['files']) - 5} more files")
            print()
        
        # Print audiobook analysis
        if audiobooks:
            print("🎧 AUDIOBOOKS FOUND:")
            print("-" * 40)
            
            for title, books in audiobooks.items():
                print(f"📖 '{title}' - {len(books)} version(s)")
                for book in books:
                    print(f"   🔹 User: {book['user_id']}, Job: {book['job_id'][:8]}..., "
                          f"Chapters: {book['chapters']}, "
                          f"Date: {book['modified'].strftime('%Y-%m-%d %H:%M')}")
                print()
            
            # Find duplicates
            duplicates = {title: books for title, books in audiobooks.items() if len(books) > 1}
            if duplicates:
                print(f"⚠️  DUPLICATES FOUND: {len(duplicates)} books have multiple versions")
                for title, books in duplicates.items():
                    print(f"   📖 '{title}': {len(books)} copies")
            else:
                print("✅ No duplicate audiobooks found")
        
        # Show if there are more objects
        if response.get('IsTruncated'):
            print(f"\n📋 Note: There are more than {max_objects} objects in the bucket")
            print("Use the cleanup script to see full analysis")
        
    except Exception as e:
        print(f"❌ Error listing bucket contents: {e}")

def main():
    print("📋 R2 Storage Content Analyzer")
    print("="*50)
    
    # Get R2 client
    r2, bucket_name = get_r2_client()
    if not r2:
        return
    
    # Test connection
    try:
        r2.head_bucket(Bucket=bucket_name)
        print(f"✅ Connected to R2 bucket: {bucket_name}")
        print()
    except Exception as e:
        print(f"❌ Cannot access bucket {bucket_name}: {e}")
        return
    
    # List contents
    list_bucket_contents(r2, bucket_name, max_objects=50)

if __name__ == "__main__":
    main()