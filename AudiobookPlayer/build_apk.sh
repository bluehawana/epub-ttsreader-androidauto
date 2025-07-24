#!/bin/bash

# Audiobook Player APK Build Script
# This script builds the Android APK for the audiobook player

echo "🚀 Building Audiobook Player APK..."

# Check if Android SDK is available
if [ -z "$ANDROID_HOME" ]; then
    echo "❌ ANDROID_HOME environment variable not set"
    echo "Please install Android SDK and set ANDROID_HOME"
    exit 1
fi

# Check if gradlew exists
if [ ! -f "./gradlew" ]; then
    echo "❌ gradlew not found. Please run this script from the project root directory"
    exit 1
fi

# Make gradlew executable
chmod +x ./gradlew

echo "📋 Cleaning previous builds..."
./gradlew clean

echo "📦 Building debug APK..."
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo "✅ Debug APK built successfully!"
    echo "📱 APK location: app/build/outputs/apk/debug/app-debug.apk"
    
    # Optional: Build release APK (requires signing)
    read -p "🔐 Build signed release APK? (requires keystore) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Building release APK..."
        ./gradlew assembleRelease
        
        if [ $? -eq 0 ]; then
            echo "✅ Release APK built successfully!"
            echo "📱 APK location: app/build/outputs/apk/release/app-release.apk"
        else
            echo "❌ Release APK build failed"
        fi
    fi
    
    echo "🎉 Build process completed!"
    echo ""
    echo "📱 Installation Instructions:"
    echo "1. Enable 'Install from Unknown Sources' on your Android device"
    echo "2. Transfer the APK file to your device"
    echo "3. Tap the APK file to install"
    echo "4. Grant storage permissions when prompted"
    echo ""
    echo "🎧 Usage:"
    echo "1. Enter your Telegram User ID (e.g., 1141127507)"
    echo "2. Tap 'Sync' to load audiobooks"
    echo "3. Download and play your audiobooks!"
    
else
    echo "❌ APK build failed"
    exit 1
fi