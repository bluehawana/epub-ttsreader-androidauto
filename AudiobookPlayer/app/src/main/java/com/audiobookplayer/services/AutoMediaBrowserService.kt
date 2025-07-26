package com.audiobookplayer.services

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.media.browse.MediaBrowser
import android.media.session.MediaSession
import android.os.Bundle
import android.os.IBinder
import android.service.media.MediaBrowserService
import android.media.MediaMetadata
import android.media.session.PlaybackState
import android.support.v4.media.MediaBrowserCompat
import android.support.v4.media.MediaDescriptionCompat
import android.support.v4.media.MediaMetadataCompat
import android.support.v4.media.session.MediaSessionCompat
import android.support.v4.media.session.PlaybackStateCompat
import com.audiobookplayer.models.Audiobook
import com.audiobookplayer.services.ApiConfig
import com.audiobookplayer.utils.FileManager
import kotlinx.coroutines.*
import android.util.Log

class AutoMediaBrowserService : MediaBrowserService() {

    private lateinit var mediaSession: MediaSessionCompat
    private lateinit var fileManager: FileManager
    private var mediaPlaybackService: MediaPlaybackService? = null
    private var serviceConnection: ServiceConnection? = null
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    
    private val audiobooks = mutableListOf<Audiobook>()
    private var currentUserId: String? = null

    companion object {
        private const val TAG = "AutoMediaBrowserService"
        private const val ROOT_ID = "root"
        private const val AUDIOBOOKS_ID = "audiobooks"
        private const val RECENT_ID = "recent"
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "AutoMediaBrowserService created")
        
        fileManager = FileManager(this)
        initializeMediaSession()
        loadUserAudiobooks()
        connectToPlaybackService()
    }

    private fun initializeMediaSession() {
        mediaSession = MediaSessionCompat(this, TAG).apply {
            setFlags(MediaSessionCompat.FLAG_HANDLES_MEDIA_BUTTONS or MediaSessionCompat.FLAG_HANDLES_TRANSPORT_CONTROLS)
            setCallback(MediaSessionCallback())
            
            val playbackState = PlaybackStateCompat.Builder()
                .setActions(PlaybackStateCompat.ACTION_PLAY_PAUSE or 
                          PlaybackStateCompat.ACTION_SKIP_TO_NEXT or 
                          PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS or
                          PlaybackStateCompat.ACTION_SEEK_TO or
                          PlaybackStateCompat.ACTION_FAST_FORWARD or
                          PlaybackStateCompat.ACTION_REWIND)
                .setState(PlaybackStateCompat.STATE_NONE, 0, 1.0f)
                .build()
            setPlaybackState(playbackState)
            
            isActive = true
        }
        
        sessionToken = mediaSession.sessionToken
    }

    private fun loadUserAudiobooks() {
        // Load saved user ID
        val prefs = getSharedPreferences("audiobook_prefs", Context.MODE_PRIVATE)
        currentUserId = prefs.getString("user_id", null)
        
        currentUserId?.let { userId ->
            serviceScope.launch {
                try {
                    val response = ApiConfig.apiService.getUserAudiobooks(userId)
                    if (response.isSuccessful && response.body() != null) {
                        audiobooks.clear()
                        audiobooks.addAll(response.body()!!.audiobooks)
                        
                        // Check which are downloaded and fetch chapter details for streaming
                        audiobooks.forEach { audiobook ->
                            audiobook.isDownloaded = fileManager.isAudiobookDownloaded(audiobook.id)
                            if (audiobook.isDownloaded) {
                                audiobook.localPath = fileManager.getAudiobookPath(audiobook.id)
                            }
                            
                            // Fetch detailed chapter information for streaming
                            try {
                                val detailsResponse = ApiConfig.apiService.getAudiobookDetails(audiobook.id)
                                if (detailsResponse.isSuccessful && detailsResponse.body() != null) {
                                    audiobook.chaptersList = detailsResponse.body()!!.chapters
                                }
                            } catch (e: Exception) {
                                Log.w(TAG, "Could not fetch chapter details for ${audiobook.id}: ${e.message}")
                            }
                        }
                        
                        Log.d(TAG, "Loaded ${audiobooks.size} audiobooks for Android Auto")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error loading audiobooks: ${e.message}")
                }
            }
        }
    }

    private fun connectToPlaybackService() {
        serviceConnection = object : ServiceConnection {
            override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
                val binder = service as MediaPlaybackService.LocalBinder
                mediaPlaybackService = binder.getService()
                Log.d(TAG, "Connected to MediaPlaybackService")
            }

            override fun onServiceDisconnected(name: ComponentName?) {
                mediaPlaybackService = null
                Log.d(TAG, "Disconnected from MediaPlaybackService")
            }
        }
        
        val intent = Intent(this, MediaPlaybackService::class.java)
        bindService(intent, serviceConnection!!, Context.BIND_AUTO_CREATE)
    }

    override fun onGetRoot(clientPackageName: String, clientUid: Int, rootHints: Bundle?): BrowserRoot? {
        Log.d(TAG, "onGetRoot called by $clientPackageName")
        
        // Allow Android Auto and Android media apps
        return when {
            clientPackageName == "com.google.android.projection.gearhead" || // Android Auto
            clientPackageName == "com.android.bluetooth" ||                   // Bluetooth
            clientPackageName.contains("android.media") -> {
                BrowserRoot(ROOT_ID, null)
            }
            else -> {
                Log.w(TAG, "Unknown client: $clientPackageName")
                BrowserRoot(ROOT_ID, null) // Allow all for now
            }
        }
    }

    override fun onLoadChildren(parentId: String, result: Result<MutableList<MediaBrowserCompat.MediaItem>>) {
        Log.d(TAG, "onLoadChildren called for $parentId")
        
        when (parentId) {
            ROOT_ID -> {
                val rootItems = mutableListOf<MediaBrowserCompat.MediaItem>()
                
                // Audiobooks category
                val audiobooksDescription = MediaDescriptionCompat.Builder()
                    .setMediaId(AUDIOBOOKS_ID)
                    .setTitle("My Audiobooks")
                    .setSubtitle("${audiobooks.size} books available")
                    .build()
                
                rootItems.add(MediaBrowserCompat.MediaItem(audiobooksDescription, MediaBrowserCompat.MediaItem.FLAG_BROWSABLE))
                
                // Recent category
                val recentDescription = MediaDescriptionCompat.Builder()
                    .setMediaId(RECENT_ID)
                    .setTitle("Recently Added")
                    .setSubtitle("Latest audiobooks")
                    .build()
                
                rootItems.add(MediaBrowserCompat.MediaItem(recentDescription, MediaBrowserCompat.MediaItem.FLAG_BROWSABLE))
                
                result.sendResult(rootItems)
            }
            
            AUDIOBOOKS_ID -> {
                val audiobookItems = mutableListOf<MediaBrowserCompat.MediaItem>()
                
                // Show all available audiobooks for streaming from R2
                audiobooks.forEach { audiobook ->
                    val description = MediaDescriptionCompat.Builder()
                        .setMediaId("audiobook_${audiobook.id}")
                        .setTitle(audiobook.title)
                        .setSubtitle("${audiobook.chapters} chapters")
                        .setDescription("Tap to play audiobook")
                        .build()
                    
                    audiobookItems.add(MediaBrowserCompat.MediaItem(description, MediaBrowserCompat.MediaItem.FLAG_PLAYABLE))
                }
                
                result.sendResult(audiobookItems)
            }
            
            RECENT_ID -> {
                val recentItems = mutableListOf<MediaBrowserCompat.MediaItem>()
                
                // Show 5 most recent downloaded audiobooks
                audiobooks.filter { it.isDownloaded }
                    .sortedByDescending { it.createdAt }
                    .take(5)
                    .forEach { audiobook ->
                        val description = MediaDescriptionCompat.Builder()
                            .setMediaId("audiobook_${audiobook.id}")
                            .setTitle(audiobook.title)
                            .setSubtitle("Recently added")
                            .setDescription("${audiobook.chapters} chapters")
                            .build()
                        
                        recentItems.add(MediaBrowserCompat.MediaItem(description, MediaBrowserCompat.MediaItem.FLAG_PLAYABLE))
                    }
                
                result.sendResult(recentItems)
            }
            
            else -> {
                result.sendResult(mutableListOf())
            }
        }
    }

    private inner class MediaSessionCallback : MediaSessionCompat.Callback() {
        
        override fun onPlayFromMediaId(mediaId: String?, extras: Bundle?) {
            Log.d(TAG, "onPlayFromMediaId: $mediaId")
            
            if (mediaId?.startsWith("audiobook_") == true) {
                val audiobookId = mediaId.removePrefix("audiobook_")
                val audiobook = audiobooks.find { it.id == audiobookId }
                
                if (audiobook != null) {
                    playAudiobook(audiobook)
                } else {
                    Log.w(TAG, "Audiobook not found or not downloaded: $audiobookId")
                }
            }
        }

        override fun onPlay() {
            Log.d(TAG, "onPlay")
            mediaPlaybackService?.play()
            updatePlaybackState(PlaybackStateCompat.STATE_PLAYING)
        }

        override fun onPause() {
            Log.d(TAG, "onPause")
            mediaPlaybackService?.pause()
            updatePlaybackState(PlaybackStateCompat.STATE_PAUSED)
        }

        override fun onStop() {
            Log.d(TAG, "onStop")
            mediaPlaybackService?.stop()
            updatePlaybackState(PlaybackStateCompat.STATE_STOPPED)
        }

        override fun onSkipToNext() {
            Log.d(TAG, "onSkipToNext")
            mediaPlaybackService?.nextChapter()
        }

        override fun onSkipToPrevious() {
            Log.d(TAG, "onSkipToPrevious")
            mediaPlaybackService?.previousChapter()
        }

        override fun onSeekTo(pos: Long) {
            Log.d(TAG, "onSeekTo: $pos")
            mediaPlaybackService?.seekTo(pos)
        }

        override fun onFastForward() {
            Log.d(TAG, "onFastForward")
            mediaPlaybackService?.seekBy(30000) // 30 seconds forward
        }

        override fun onRewind() {
            Log.d(TAG, "onRewind")
            mediaPlaybackService?.seekBy(-30000) // 30 seconds backward
        }

        override fun onSetPlaybackSpeed(speed: Float) {
            Log.d(TAG, "onSetPlaybackSpeed: $speed")
            mediaPlaybackService?.setPlaybackSpeed(speed)
        }
    }

    private fun playAudiobook(audiobook: Audiobook) {
        Log.d(TAG, "Playing audiobook: ${audiobook.title}")
        
        mediaPlaybackService?.loadAudiobook(audiobook)
        
        // Update metadata
        val metadata = MediaMetadataCompat.Builder()
            .putString(MediaMetadataCompat.METADATA_KEY_MEDIA_ID, "audiobook_${audiobook.id}")
            .putString(MediaMetadataCompat.METADATA_KEY_TITLE, audiobook.title)
            .putString(MediaMetadataCompat.METADATA_KEY_ARTIST, "Audiobook")
            .putString(MediaMetadataCompat.METADATA_KEY_ALBUM, "My Audiobooks")
            .putLong(MediaMetadataCompat.METADATA_KEY_DURATION, audiobook.totalDuration?.toLong() ?: 0)
            .build()
        
        mediaSession.setMetadata(metadata)
        updatePlaybackState(PlaybackStateCompat.STATE_PLAYING)
    }

    private fun updatePlaybackState(state: Int) {
        val position = mediaPlaybackService?.getCurrentPosition()?.toLong() ?: 0
        val playbackState = PlaybackStateCompat.Builder()
            .setActions(PlaybackStateCompat.ACTION_PLAY_PAUSE or 
                      PlaybackStateCompat.ACTION_SKIP_TO_NEXT or 
                      PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS or
                      PlaybackStateCompat.ACTION_SEEK_TO or
                      PlaybackStateCompat.ACTION_FAST_FORWARD or
                      PlaybackStateCompat.ACTION_REWIND or
                      PlaybackStateCompat.ACTION_SET_PLAYBACK_SPEED)
            .setState(state, position, 1.0f)
            .build()
        
        mediaSession.setPlaybackState(playbackState)
    }

    override fun onDestroy() {
        Log.d(TAG, "AutoMediaBrowserService destroyed")
        serviceConnection?.let { unbindService(it) }
        mediaSession.release()
        serviceScope.cancel()
        super.onDestroy()
    }
}