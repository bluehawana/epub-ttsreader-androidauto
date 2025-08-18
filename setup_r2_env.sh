#!/bin/bash

echo "🔧 Setting up R2 Environment Variables"
echo "======================================"

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📄 Found .env file, loading existing variables..."
    source .env
fi

# Set R2 endpoint (replace with your actual endpoint)
# export R2_ENDPOINT_URL="https://your-account-id.r2.cloudflarestorage.com"
# export R2_BUCKET_NAME="ebuppool"

echo "⚠️  Please set your R2 credentials manually:"
echo "export R2_ENDPOINT_URL='https://your-account-id.r2.cloudflarestorage.com'"
echo "✅ R2_BUCKET_NAME set to: $R2_BUCKET_NAME"

# Check if access keys are set
if [ -z "$R2_ACCESS_KEY_ID" ]; then
    echo ""
    echo "⚠️  R2_ACCESS_KEY_ID not found"
    echo "Please set your R2 access key:"
    echo "export R2_ACCESS_KEY_ID='your_access_key_here'"
else
    echo "✅ R2_ACCESS_KEY_ID is set"
fi

if [ -z "$R2_SECRET_ACCESS_KEY" ]; then
    echo ""
    echo "⚠️  R2_SECRET_ACCESS_KEY not found"
    echo "Please set your R2 secret key:"
    echo "export R2_SECRET_ACCESS_KEY='your_secret_key_here'"
else
    echo "✅ R2_SECRET_ACCESS_KEY is set"
fi

echo ""
echo "🚀 To use the R2 cleanup tools:"
echo "1. Set your R2 credentials (if not already set):"
echo "   export R2_ACCESS_KEY_ID='your_access_key'"
echo "   export R2_SECRET_ACCESS_KEY='your_secret_key'"
echo ""
echo "2. Run the analyzer:"
echo "   python3 list_r2_contents.py"
echo ""
echo "3. Run the cleanup tool:"
echo "   python3 cleanup_r2_storage.py"
echo ""
echo "💡 Your R2 bucket structure should be:"
echo "   ebuppool/"
echo "   ├── 1141127507/           # Your user ID"
echo "   │   ├── epubs/            # Original EPUB files"
echo "   │   ├── job_id_1/         # Audiobook 1"
echo "   │   │   ├── metadata.json"
echo "   │   │   ├── chapter_1.mp3"
echo "   │   │   └── chapter_2.mp3"
echo "   │   └── job_id_2/         # Audiobook 2"
echo "   └── other_user_id/"