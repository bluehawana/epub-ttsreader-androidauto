#!/bin/bash

echo "🔨 Building AudiobookPlayer Debug APK..."

cd AudiobookPlayer

# Clean previous builds
echo "🧹 Cleaning previous builds..."
./gradlew clean

# Build debug APK
echo "📱 Building debug APK..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📦 APK location: app/build/outputs/apk/debug/app-debug.apk"
    
    # Show APK info
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        echo "📊 APK size: $(du -h "$APK_PATH" | cut -f1)"
        echo "🎯 Ready to install and test!"
    fi
else
    echo "❌ Build failed!"
    exit 1
fi