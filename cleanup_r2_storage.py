#!/usr/bin/env python3
"""
Cloudflare R2 Storage Cleanup Script
Analyzes and cleans up duplicate audiobooks in R2 storage
"""

import os
import json
import boto3
from collections import defaultdict
from datetime import datetime
import hashlib

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
        print("Please set: R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
        return None, None
    
    r2 = boto3.client(
        's3',
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
        region_name='auto'
    )
    
    return r2, r2_bucket

def analyze_storage_structure(r2, bucket_name):
    """Analyze the current storage structure"""
    print("🔍 Analyzing R2 storage structure...")
    
    try:
        response = r2.list_objects_v2(Bucket=bucket_name, Prefix="")
        objects = response.get('Contents', [])
        
        # Continue pagination if needed
        while response.get('IsTruncated'):
            response = r2.list_objects_v2(
                Bucket=bucket_name, 
                Prefix="",
                ContinuationToken=response['NextContinuationToken']
            )
            objects.extend(response.get('Contents', []))
        
        print(f"📊 Total objects found: {len(objects)}")
        
        # Analyze structure
        users = defaultdict(lambda: {'audiobooks': defaultdict(list), 'epubs': [], 'other': []})
        audiobooks_by_title = defaultdict(list)
        
        for obj in objects:
            key = obj['Key']
            size = obj['Size']
            modified = obj['LastModified']
            
            parts = key.split('/')
            
            if len(parts) >= 2:
                user_id = parts[0]
                
                if len(parts) >= 3 and parts[1] == 'epubs':
                    # EPUB files: user_id/epubs/filename.epub
                    users[user_id]['epubs'].append({
                        'key': key,
                        'filename': parts[2],
                        'size': size,
                        'modified': modified
                    })
                elif len(parts) >= 3 and key.endswith('metadata.json'):
                    # Audiobook metadata: user_id/job_id/metadata.json
                    job_id = parts[1]
                    try:
                        # Get metadata to find book title
                        metadata_obj = r2.get_object(Bucket=bucket_name, Key=key)
                        metadata = json.loads(metadata_obj['Body'].read())
                        book_title = metadata.get('book_title', 'Unknown')
                        
                        audiobook_info = {
                            'job_id': job_id,
                            'title': book_title,
                            'key': key,
                            'size': size,
                            'modified': modified,
                            'chapters': len(metadata.get('chapters', []))
                        }
                        
                        users[user_id]['audiobooks'][job_id].append(audiobook_info)
                        audiobooks_by_title[book_title].append(audiobook_info)
                        
                    except Exception as e:
                        print(f"⚠️  Could not read metadata for {key}: {e}")
                elif len(parts) >= 3 and key.endswith('.mp3'):
                    # Audio files: user_id/job_id/chapter_X.mp3
                    job_id = parts[1]
                    users[user_id]['audiobooks'][job_id].append({
                        'key': key,
                        'filename': parts[2],
                        'size': size,
                        'modified': modified,
                        'type': 'audio'
                    })
                else:
                    users[user_id]['other'].append({
                        'key': key,
                        'size': size,
                        'modified': modified
                    })
        
        return users, audiobooks_by_title
        
    except Exception as e:
        print(f"❌ Error analyzing storage: {e}")
        return None, None

def print_analysis_report(users, audiobooks_by_title):
    """Print detailed analysis report"""
    print("\n" + "="*60)
    print("📋 STORAGE ANALYSIS REPORT")
    print("="*60)
    
    total_size = 0
    total_audiobooks = 0
    total_epubs = 0
    
    for user_id, user_data in users.items():
        print(f"\n👤 User: {user_id}")
        
        # EPUBs
        epub_count = len(user_data['epubs'])
        epub_size = sum(item['size'] for item in user_data['epubs'])
        print(f"   📚 EPUBs: {epub_count} files ({epub_size / 1024 / 1024:.1f} MB)")
        
        # Audiobooks
        audiobook_count = len(user_data['audiobooks'])
        audiobook_size = 0
        for job_id, items in user_data['audiobooks'].items():
            audiobook_size += sum(item['size'] for item in items)
        
        print(f"   🎧 Audiobooks: {audiobook_count} books ({audiobook_size / 1024 / 1024:.1f} MB)")
        
        # Other files
        other_count = len(user_data['other'])
        other_size = sum(item['size'] for item in user_data['other'])
        if other_count > 0:
            print(f"   📄 Other files: {other_count} files ({other_size / 1024 / 1024:.1f} MB)")
        
        total_size += epub_size + audiobook_size + other_size
        total_audiobooks += audiobook_count
        total_epubs += epub_count
    
    print(f"\n📊 TOTALS:")
    print(f"   📚 Total EPUBs: {total_epubs}")
    print(f"   🎧 Total Audiobooks: {total_audiobooks}")
    print(f"   💾 Total Storage: {total_size / 1024 / 1024 / 1024:.2f} GB")
    
    # Find duplicates
    print(f"\n🔍 DUPLICATE ANALYSIS:")
    duplicates = {title: books for title, books in audiobooks_by_title.items() if len(books) > 1}
    
    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} books with duplicates:")
        for title, books in duplicates.items():
            print(f"      📖 '{title}': {len(books)} copies")
            for book in books:
                print(f"         - Job ID: {book['job_id']} ({book['modified'].strftime('%Y-%m-%d %H:%M')})")
    else:
        print("   ✅ No duplicates found!")

def create_cleanup_plan(users, audiobooks_by_title):
    """Create a cleanup plan for duplicates"""
    cleanup_plan = {
        'keep': [],
        'delete': [],
        'total_savings': 0
    }
    
    # Find duplicates and plan cleanup
    duplicates = {title: books for title, books in audiobooks_by_title.items() if len(books) > 1}
    
    for title, books in duplicates.items():
        # Sort by modification date (keep newest)
        books_sorted = sorted(books, key=lambda x: x['modified'], reverse=True)
        
        # Keep the newest one
        keep_book = books_sorted[0]
        cleanup_plan['keep'].append(keep_book)
        
        # Mark others for deletion
        for book in books_sorted[1:]:
            cleanup_plan['delete'].append(book)
            cleanup_plan['total_savings'] += book['size']
    
    return cleanup_plan

def execute_cleanup(r2, bucket_name, cleanup_plan, dry_run=True):
    """Execute the cleanup plan"""
    if dry_run:
        print("\n🧪 DRY RUN - No files will be deleted")
    else:
        print("\n🗑️  EXECUTING CLEANUP")
    
    print("="*60)
    
    deleted_count = 0
    deleted_size = 0
    
    for book in cleanup_plan['delete']:
        job_id = book['job_id']
        user_id = None
        
        # Find user_id from the key
        if 'key' in book:
            user_id = book['key'].split('/')[0]
        
        if user_id:
            # Delete entire job folder (all files for this audiobook)
            prefix = f"{user_id}/{job_id}/"
            
            try:
                # List all objects with this prefix
                response = r2.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
                objects_to_delete = response.get('Contents', [])
                
                if objects_to_delete:
                    print(f"📖 {book['title']} (Job: {job_id})")
                    print(f"   📁 Deleting {len(objects_to_delete)} files from {prefix}")
                    
                    if not dry_run:
                        # Delete objects in batches
                        for i in range(0, len(objects_to_delete), 1000):
                            batch = objects_to_delete[i:i+1000]
                            delete_objects = [{'Key': obj['Key']} for obj in batch]
                            
                            r2.delete_objects(
                                Bucket=bucket_name,
                                Delete={'Objects': delete_objects}
                            )
                    
                    batch_size = sum(obj['Size'] for obj in objects_to_delete)
                    deleted_count += len(objects_to_delete)
                    deleted_size += batch_size
                    
                    print(f"   💾 Freed: {batch_size / 1024 / 1024:.1f} MB")
                
            except Exception as e:
                print(f"   ❌ Error deleting {prefix}: {e}")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   🗑️  Files deleted: {deleted_count}")
    print(f"   💾 Space freed: {deleted_size / 1024 / 1024:.1f} MB")
    print(f"   📖 Books kept: {len(cleanup_plan['keep'])}")

def main():
    """Main cleanup function"""
    print("🧹 Cloudflare R2 Storage Cleanup Tool")
    print("="*60)
    
    # Get R2 client
    r2, bucket_name = get_r2_client()
    if not r2:
        return
    
    print(f"🪣 Bucket: {bucket_name}")
    
    # Analyze storage
    users, audiobooks_by_title = analyze_storage_structure(r2, bucket_name)
    if not users:
        return
    
    # Print analysis
    print_analysis_report(users, audiobooks_by_title)
    
    # Create cleanup plan
    cleanup_plan = create_cleanup_plan(users, audiobooks_by_title)
    
    if cleanup_plan['delete']:
        print(f"\n🧹 CLEANUP PLAN:")
        print(f"   📖 Books to keep: {len(cleanup_plan['keep'])}")
        print(f"   🗑️  Books to delete: {len(cleanup_plan['delete'])}")
        print(f"   💾 Space to free: {cleanup_plan['total_savings'] / 1024 / 1024:.1f} MB")
        
        # Ask for confirmation
        print(f"\n⚠️  This will delete {len(cleanup_plan['delete'])} duplicate audiobooks!")
        choice = input("Continue? (y/N): ").lower().strip()
        
        if choice == 'y':
            # First do a dry run
            print("\n1️⃣ Performing dry run...")
            execute_cleanup(r2, bucket_name, cleanup_plan, dry_run=True)
            
            # Ask for final confirmation
            final_choice = input("\nProceed with actual deletion? (y/N): ").lower().strip()
            if final_choice == 'y':
                print("\n2️⃣ Executing cleanup...")
                execute_cleanup(r2, bucket_name, cleanup_plan, dry_run=False)
                print("\n✅ Cleanup completed!")
            else:
                print("\n❌ Cleanup cancelled.")
        else:
            print("\n❌ Cleanup cancelled.")
    else:
        print("\n✅ No cleanup needed - no duplicates found!")

if __name__ == "__main__":
    main()