#!/bin/bash
# Heroku Deployment Script for EPUB Audiobook Service with Cloudflare R2

echo "🚀 Deploying EPUB Audiobook Service to Heroku (R2 Storage)..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "   brew tap heroku/brew && brew install heroku"
    exit 1
fi

# Login to Heroku (if not already logged in)
echo "📝 Checking Heroku authentication..."
heroku auth:whoami || {
    echo "Please login to Heroku:"
    heroku login
}

# Create Heroku app
APP_NAME="epub-audiobook-r2"
echo "🏗️  Creating Heroku app: $APP_NAME"
heroku create $APP_NAME --region us

# No database or S3 addons needed - we use Cloudflare R2!
echo "📦 Using Cloudflare R2 for storage (no Heroku addons needed)"

# Set environment variables
echo "⚙️  Setting environment variables..."

# Set Telegram bot token
heroku config:set TELEGRAM_BOT_TOKEN=8043237984:AAGOCQYtGyxTr9Jrwk6u9bN2bkoWts-qAFQ --app $APP_NAME

echo "⚠️  MANUAL SETUP REQUIRED:"
echo "   1. Create Cloudflare R2 bucket at: https://dash.cloudflare.com/r2"
echo "   2. Get R2 API credentials and set:"
echo "   heroku config:set R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com --app $APP_NAME"
echo "   heroku config:set R2_ACCESS_KEY_ID=your_key --app $APP_NAME"
echo "   heroku config:set R2_SECRET_ACCESS_KEY=your_secret --app $APP_NAME"
echo "   heroku config:set R2_BUCKET_NAME=your_bucket_name --app $APP_NAME"
echo ""
echo "   3. Optional - Set Azure Speech API key for better TTS:"
echo "   heroku config:set AZURE_SPEECH_KEY=your_key_here --app $APP_NAME"
echo ""

# Deploy to Heroku
echo "🚀 Deploying application..."
git add .
git commit -m "Simplify to Cloudflare R2 storage - no database needed"
heroku git:remote -a $APP_NAME
git push heroku main

echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_NAME.herokuapp.com"
echo "📊 View logs: heroku logs --tail --app $APP_NAME"
echo ""
echo "💡 Benefits of R2 storage:"
echo "   ✅ No database costs"
echo "   ✅ Cheaper than S3"
echo "   ✅ Simple file storage"
echo "   ✅ Global CDN included"

heroku open --app $APP_NAME