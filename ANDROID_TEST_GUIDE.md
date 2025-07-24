# Android Auto App Testing Guide

## 🚗 How to Test Your Android Auto App

### Step 1: Setup Android Emulator with Android Auto

```bash
# 1. Open Android Studio
# 2. Create a new AVD (Android Virtual Device)
# 3. Choose API 30+ with Google APIs
# 4. Enable Hardware Profile: Automotive (1024 x 768 hdpi)

# Or use existing phone emulator and install Android Auto
```

### Step 2: Install Android Auto Desktop Head Unit

```bash
# Download from: https://developer.android.com/training/cars/testing
# This simulates a car's infotainment system
```

### Step 3: Test Your App

1. **Build and Install Your App:**
   ```bash
   cd /path/to/your/audiobook-car-player
   ./gradlew assembleDebug
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

2. **Connect to Backend:**
   - Update your app's `BASE_URL` to: `https://epub-audiobook-service-ab00bb696e09.herokuapp.com`
   - Test API calls from the app

3. **Test QR Code Authentication:**
   - Generate QR code with user ID
   - Scan with app
   - Verify connection to backend

### Step 4: Test Complete Flow

1. **Send EPUB via Telegram Bot**
2. **Check Backend Processing:**
   ```bash
   curl "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/api/audiobooks/YOUR_USER_ID"
   ```
3. **Open Android Auto App**
4. **Browse audiobooks and play**

### Step 5: Debug Issues

**Check Backend Logs:**
```bash
heroku logs --tail --app epub-audiobook-service
```

**Check Android App Logs:**
```bash
adb logcat | grep "AudiobookCarPlayer"
```

**Test API Endpoints:**
```bash
# Test health
curl "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/health"

# Test user audiobooks
curl "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/api/audiobooks/test_user_123"

# Test download
curl "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/api/download/AUDIOBOOK_ID"
```

## 🎯 Expected Test Results

1. ✅ **Backend Health**: R2 connected, TTS available
2. ✅ **Telegram Bot**: Sends EPUB to backend successfully  
3. ✅ **TTS Processing**: Converts text to MP3 in R2
4. ✅ **Android App**: Fetches audiobooks from API
5. ✅ **Audio Playback**: Streams MP3 from R2 URLs

## 🐛 Common Issues

**"No audiobooks found"**
- Check user_id matches between Telegram and Android app
- Verify EPUB processing completed successfully

**"Audio won't play"**
- Check R2 bucket public access settings
- Verify MP3 URLs are accessible
- Test direct URL in browser

**"App crashes"**
- Check Android logs for exceptions
- Verify API response format matches app expectations

## 📊 Success Criteria

Your system works when:
1. Telegram bot receives EPUB → Backend processes → R2 stores MP3s
2. Android Auto app shows audiobooks list
3. Audio plays smoothly in car interface
4. Navigation (play/pause/next/previous) works