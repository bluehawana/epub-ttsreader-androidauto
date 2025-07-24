#!/bin/bash
# Complete Testing Script for EPUB Audiobook System

echo "🚀 EPUB Audiobook System - Complete Test"
echo "========================================"

# Test 1: Backend Health
echo "📊 1. Testing Backend Health..."
HEALTH=$(curl -s "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/health")
echo "Response: $HEALTH"

if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Test 2: Check R2 Storage Connection
if echo "$HEALTH" | grep -q "cloudflare_r2_connected"; then
    echo "✅ R2 storage is connected"
else
    echo "❌ R2 storage not connected"
fi

# Test 3: Check TTS Service
if echo "$HEALTH" | grep -q '"tts":"edge"'; then
    echo "✅ Edge TTS is available (Azure TTS fallback)"
elif echo "$HEALTH" | grep -q '"tts":"azure"'; then
    echo "✅ Azure TTS is connected"
else
    echo "❌ No TTS service available"
fi

echo ""
echo "🔧 Next Steps for Complete Testing:"
echo "1. Test Telegram Bot (see test_telegram.py)"
echo "2. Test Android Auto App (see android_test_guide.md)"
echo "3. Run end-to-end test (see e2e_test.py)"