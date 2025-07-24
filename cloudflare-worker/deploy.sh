#!/bin/bash
# Deploy EPUB Audiobook CF Worker

echo "🚀 Deploying EPUB Audiobook Cloudflare Worker..."

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Deploy to Cloudflare
echo "🌐 Deploying to Cloudflare..."
wrangler deploy

echo "✅ Deployment complete!"
echo ""
echo "🔗 Your worker is now available at:"
echo "   https://epub-audiobook-worker.your-subdomain.workers.dev"
echo ""
echo "📱 Update your Android app's ApiConfig.BASE_URL to use the worker URL"
echo ""
echo "🎯 Test endpoints:"
echo "   GET  /health"
echo "   POST /api/process-epub"
echo "   GET  /api/audiobooks/{userId}"