#!/usr/bin/env python3
"""
Check R2 buckets and create the required bucket if needed
"""
import boto3
from dotenv import load_dotenv
import os

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
            region_name='auto'  # Cloudflare R2 uses 'auto'
        )
        return r2
    return None

def main():
    r2 = get_r2_client()
    if not r2:
        print("❌ R2 client not configured")
        return
    
    bucket_name = os.environ.get('R2_BUCKET_NAME', 'epub-audiobook-storage')
    
    try:
        # List existing buckets
        print("📋 Existing R2 buckets:")
        response = r2.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        for bucket in buckets:
            print(f"  ✅ {bucket}")
        
        # Check if our bucket exists
        if bucket_name in buckets:
            print(f"\n✅ Bucket '{bucket_name}' already exists!")
        else:
            print(f"\n❌ Bucket '{bucket_name}' does not exist")
            print(f"🔧 Creating bucket '{bucket_name}'...")
            
            # Create the bucket
            r2.create_bucket(Bucket=bucket_name)
            print(f"✅ Successfully created bucket '{bucket_name}'!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Available bucket names from your account:")
        try:
            response = r2.list_buckets()
            for bucket in response['Buckets']:
                print(f"  - {bucket['Name']}")
        except:
            print("  Could not list buckets")

if __name__ == '__main__':
    main()