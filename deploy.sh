#!/bin/bash
# Heroku Deployment Script for EPUB Audiobook Service

echo "🚀 Deploying EPUB Audiobook Service to Heroku..."

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
APP_NAME="epub-audiobook-service"
echo "🏗️  Creating Heroku app: $APP_NAME"
heroku create $APP_NAME --region us

# Add JawsDB MySQL addon (much cheaper than PostgreSQL!)
echo "🗄️  Adding JawsDB MySQL database..."
heroku addons:create jawsdb:kitefin --app $APP_NAME

# Add S3 file storage (using Bucketeer addon)
echo "📦 Adding S3 file storage..."
heroku addons:create bucketeer:hobbyist --app $APP_NAME

# Set environment variables
echo "⚙️  Setting environment variables..."

# You'll need to set these manually:
echo "⚠️  MANUAL SETUP REQUIRED:"
echo "   Set your Azure Speech API key:"
echo "   heroku config:set AZURE_SPEECH_KEY=your_key_here --app $APP_NAME"
echo "   heroku config:set AZURE_SPEECH_REGION=eastus --app $APP_NAME"
echo ""
echo "   Set your Telegram bot token:"
echo "   heroku config:set TELEGRAM_BOT_TOKEN=8043237984:AAGOCQYtGyxTr9Jrwk6u9bN2bkoWts-qAFQ --app $APP_NAME"
echo ""

# Deploy to Heroku
echo "🚀 Deploying application..."
git add .
git commit -m "Deploy EPUB audiobook service to Heroku with MySQL"
heroku git:remote -a $APP_NAME
git push heroku main

# Run database migrations
echo "🗄️  Setting up MySQL database schema..."
# Get JawsDB connection details and run schema
heroku config:get JAWSDB_URL --app $APP_NAME
echo "Run this command to set up the database:"
echo "mysql -h <host> -u <user> -p<password> <database> < schema.sql"

# Open the deployed app
echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_NAME.herokuapp.com"
echo "📊 View logs: heroku logs --tail --app $APP_NAME"

heroku open --app $APP_NAME