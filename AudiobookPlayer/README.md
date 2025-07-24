# Audiobook Player Android App

A modern Android application for syncing and playing audiobooks from your Heroku backend service.

## Features

### 📚 **Audiobook Management**
- Sync audiobooks from Heroku backend by User ID
- Download audiobooks for offline playback
- Delete local files to save storage
- View audiobook details (title, author, chapters)

### 🎧 **Advanced Media Player**
- Play/Pause controls
- Chapter navigation (previous/next)
- 30-second rewind/forward
- Variable playback speed (0.5x to 2.0x)
- Volume control and mute
- Seek bar for precise position control
- Sleep timer support
- Bookmark functionality

### 💾 **File Management**
- Automatic download management
- Storage usage tracking
- Individual audiobook deletion
- Chapter-based file organization

### 🎨 **Modern UI**
- Material Design 3
- Dark/Light theme support
- Intuitive navigation
- Progress indicators
- Empty states and loading states

## Setup Instructions

### Prerequisites
- Android Studio Arctic Fox or later
- Android SDK 24+ (Android 7.0)
- Kotlin 1.8+

### Configuration

1. **Backend URL**: The app connects to your Heroku backend at:
   ```
   https://epub-audiobook-service-ab00bb696e09.herokuapp.com/
   ```

2. **User ID**: Enter your Telegram User ID (e.g., `1141127507`) to sync audiobooks

### Build Instructions

1. **Clone/Copy the project files**
2. **Open in Android Studio**
3. **Sync project with Gradle files**
4. **Build APK**:
   ```bash
   ./gradlew assembleRelease
   ```

### Installation

1. Enable "Install from Unknown Sources" on your Android device
2. Install the generated APK file
3. Grant storage permissions when prompted

## Usage

### Getting Started
1. **Launch the app**
2. **Enter your Telegram User ID** (the same ID used with the Telegram bot)
3. **Tap "Sync"** to load your audiobooks from the backend
4. **Download audiobooks** for offline playback
5. **Tap "Play"** to start listening

### Player Controls
- **Play/Pause**: Main control button
- **Chapter Navigation**: Skip to previous/next chapter
- **Seek**: Drag the progress bar or use 30s rewind/forward buttons
- **Speed Control**: Tap speed button to cycle through speeds
- **Volume**: Tap volume icon to mute/unmute
- **Sleep Timer**: Set automatic playback stop
- **Bookmarks**: Save your current position

### File Management
- **Download**: Tap download button to save audiobook locally
- **Delete**: Use the menu (⋮) to delete local files
- **Storage**: Check total storage usage in settings

## Technical Details

### Architecture
- **MVVM Pattern**: Clean separation of concerns
- **Retrofit**: HTTP client for backend communication
- **ExoPlayer**: Advanced media playback
- **Room Database**: Local data persistence
- **Kotlin Coroutines**: Asynchronous operations

### API Integration
The app connects to your backend endpoints:
- `GET /api/audiobooks/{userId}` - List user's audiobooks
- `GET /api/download/{audiobookId}` - Get audiobook details and download URLs
- `GET /health` - Backend health check

### File Structure
```
AudiobookPlayer/
├── app/
│   ├── src/main/
│   │   ├── java/com/audiobookplayer/
│   │   │   ├── activities/     # UI Activities
│   │   │   ├── adapters/       # RecyclerView Adapters
│   │   │   ├── models/         # Data Models
│   │   │   ├── services/       # API & Media Services
│   │   │   └── utils/          # Utility Classes
│   │   ├── res/
│   │   │   ├── layout/         # XML Layouts
│   │   │   ├── values/         # Colors, Strings, Styles
│   │   │   └── drawable/       # Icons & Backgrounds
│   │   └── AndroidManifest.xml
│   └── build.gradle
└── build.gradle
```

## Permissions Required
- **INTERNET**: Sync audiobooks from backend
- **ACCESS_NETWORK_STATE**: Check network connectivity
- **WRITE_EXTERNAL_STORAGE**: Download audiobook files
- **READ_EXTERNAL_STORAGE**: Access downloaded files
- **WAKE_LOCK**: Keep device awake during playback
- **FOREGROUND_SERVICE**: Background media playback

## Troubleshooting

### Common Issues
1. **No audiobooks appear**: Check your User ID and internet connection
2. **Download fails**: Ensure storage permission is granted
3. **Playback issues**: Check if files downloaded completely
4. **Sync errors**: Verify backend is running and accessible

### Support
For technical support or feature requests, contact the development team.

## Version History
- **v1.0.0**: Initial release with core functionality
  - Audiobook sync and download
  - Advanced media player
  - File management
  - Material Design UI