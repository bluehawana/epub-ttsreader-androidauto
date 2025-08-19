package com.audiobookplayer.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.MediaPlayer
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.support.v4.media.session.MediaSessionCompat
import android.support.v4.media.session.PlaybackStateCompat
import androidx.core.app.NotificationCompat
import com.audiobookplayer.R
import com.audiobookplayer.activities.PlayerActivity
import com.audiobookplayer.models.Audiobook
import com.audiobookplayer.utils.FileManager
import java.io.File

class MediaPlaybackService : Service() {
    
    private val binder = LocalBinder()
    private var mediaPlayer: MediaPlayer? = null
    private lateinit var fileManager: FileManager
    private var currentAudiobook: Audiobook? = null
    private var currentChapter = 0
    private var mediaSession: MediaSessionCompat? = null
    private var notificationManager: NotificationManager? = null
    private var shouldStartWhenPrepared = false
    
    // Progress tracking
    private var progressUpdateHandler: android.os.Handler? = null
    private var progressUpdateRunnable: Runnable? = null
    private var progressCallback: ((Int, Int) -> Unit)? = null
    
    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "audiobook_playback"
    }
    
    inner class LocalBinder : Binder() {
        fun getService(): MediaPlaybackService = this@MediaPlaybackService
    }

    override fun onCreate() {
        super.onCreate()
        fileManager = FileManager(this)
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannel()
        
        // Initialize progress tracking
        progressUpdateHandler = android.os.Handler(android.os.Looper.getMainLooper())
        setupProgressUpdates()
    }

    override fun onBind(intent: Intent): IBinder {
        return binder
    }

    fun loadAudiobook(audiobook: Audiobook) {
        android.util.Log.d("MediaPlaybackService", "loadAudiobook() called")
        android.util.Log.d("MediaPlaybackService", "Audiobook: ${audiobook.title}")
        android.util.Log.d("MediaPlaybackService", "Current chapter: ${audiobook.currentChapter}")
        android.util.Log.d("MediaPlaybackService", "Chapters list size: ${audiobook.chaptersList.size}")
        
        currentAudiobook = audiobook
        currentChapter = audiobook.currentChapter
        loadChapter(currentChapter)
    }
    
    fun loadChapter(chapterIndex: Int) {
        currentAudiobook?.let { audiobook ->
            // Debug logging
            android.util.Log.d("MediaPlaybackService", "loadChapter: index=$chapterIndex, chapters.size=${audiobook.chaptersList.size}")
            
            if (chapterIndex >= 0 && chapterIndex < audiobook.chaptersList.size) {
                val chapter = audiobook.chaptersList[chapterIndex]
                android.util.Log.d("MediaPlaybackService", "Loading chapter: ${chapter.title}, URL: ${chapter.url}")
                
                // Use R2 URL for streaming if available, otherwise try local file
                if (chapter.url.isNotEmpty()) {
                    loadAudioFromUrlWithFallback(chapter)
                } else {
                    // Fallback to local file if URL not available
                    val chapterFiles = fileManager.getChapterFiles(audiobook.id)
                    if (chapterIndex < chapterFiles.size) {
                        val chapterFile = chapterFiles[chapterIndex]
                        loadAudioFile(chapterFile)
                    }
                }
                currentChapter = chapterIndex
            } else {
                android.util.Log.w("MediaPlaybackService", "Invalid chapter index: $chapterIndex (max: ${audiobook.chaptersList.size})")
            }
        }
    }
    
    private fun loadAudioFile(file: File) {
        mediaPlayer?.release()
        mediaPlayer = MediaPlayer().apply {
            try {
                setDataSource(file.absolutePath)
                prepareAsync()
                setOnPreparedListener {
                    // Ready to play
                }
                setOnCompletionListener {
                    // Chapter completed, move to next
                    nextChapter()
                }
                setOnErrorListener { _, what, extra ->
                    // Handle error
                    false
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    private fun loadAudioFromUrlWithFallback(chapter: com.audiobookplayer.models.Chapter) {
        android.util.Log.d("MediaPlaybackService", "loadAudioFromUrlWithFallback: ${chapter.url}")
        
        // Try primary URL with retry logic
        loadAudioFromUrlWithRetry(chapter.url, maxRetries = 2) { success ->
            if (!success) {
                android.util.Log.w("MediaPlaybackService", "Primary URL failed after retries, trying direct R2 URL")
                // Try direct R2 URL as fallback
                val directR2Url = generateDirectR2Url(chapter.r2_key)
                if (directR2Url != null) {
                    loadAudioFromUrlWithRetry(directR2Url, maxRetries = 1) { fallbackSuccess ->
                        if (!fallbackSuccess) {
                            android.util.Log.e("MediaPlaybackService", "Both URLs failed for chapter: ${chapter.title}")
                            // Show error to user instead of auto-skipping
                            notifyPlaybackError("Failed to load chapter: ${chapter.title}")
                        }
                    }
                } else {
                    android.util.Log.e("MediaPlaybackService", "No fallback URL available for chapter: ${chapter.title}")
                    notifyPlaybackError("No valid URL for chapter: ${chapter.title}")
                }
            }
        }
    }
    
    private fun loadAudioFromUrlWithRetry(url: String, maxRetries: Int, callback: ((Boolean) -> Unit)? = null) {
        var retryCount = 0
        
        fun attemptLoad() {
            android.util.Log.d("MediaPlaybackService", "Attempting to load URL (attempt ${retryCount + 1}/$maxRetries): $url")
            
            loadAudioFromUrl(url) { success ->
                if (success) {
                    callback?.invoke(true)
                } else if (retryCount < maxRetries - 1) {
                    retryCount++
                    android.util.Log.w("MediaPlaybackService", "Load failed, retrying in 2 seconds...")
                    // Retry after 2 seconds
                    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                        attemptLoad()
                    }, 2000)
                } else {
                    android.util.Log.e("MediaPlaybackService", "All retry attempts failed for URL: $url")
                    callback?.invoke(false)
                }
            }
        }
        
        attemptLoad()
    }
    
    private fun notifyPlaybackError(message: String) {
        android.util.Log.e("MediaPlaybackService", "Playback error: $message")
        // You could broadcast this error to the UI or show a notification
        // For now, just log it
    }
    
    private fun setupProgressUpdates() {
        progressUpdateRunnable = object : Runnable {
            override fun run() {
                mediaPlayer?.let { player ->
                    if (player.isPlaying) {
                        val currentPosition = player.currentPosition
                        val duration = try { player.duration } catch (e: Exception) { 0 }
                        
                        // Notify callback with current position and duration
                        progressCallback?.invoke(currentPosition, duration)
                        
                        // Schedule next update in 1 second
                        progressUpdateHandler?.postDelayed(this, 1000)
                    }
                }
            }
        }
    }
    
    private fun startProgressUpdates() {
        stopProgressUpdates()
        progressUpdateHandler?.post(progressUpdateRunnable!!)
    }
    
    private fun stopProgressUpdates() {
        progressUpdateRunnable?.let { runnable ->
            progressUpdateHandler?.removeCallbacks(runnable)
        }
    }
    
    fun setProgressCallback(callback: (Int, Int) -> Unit) {
        progressCallback = callback
    }
    
    private fun generateDirectR2Url(r2Key: String): String? {
        // Extract bucket name from environment or use default
        // Format: https://pub-{bucket}.r2.dev/{r2_key}
        return try {
            // This would need to be configured based on your R2 setup
            "https://pub-your-bucket-name.r2.dev/$r2Key"
        } catch (e: Exception) {
            android.util.Log.w("MediaPlaybackService", "Could not generate direct R2 URL: $e")
            null
        }
    }
    
    private fun loadAudioFromUrl(url: String, callback: ((Boolean) -> Unit)? = null) {
        android.util.Log.d("MediaPlaybackService", "loadAudioFromUrl: Starting to load URL: $url")
        mediaPlayer?.release()
        mediaPlayer = MediaPlayer().apply {
            try {
                android.util.Log.d("MediaPlaybackService", "Setting data source: $url")
                
                // For HTTP URLs, use string-based setDataSource which works better with streaming
                if (url.startsWith("http")) {
                    setDataSource(url)
                } else {
                    // For local files, use URI-based approach
                    setDataSource(this@MediaPlaybackService, android.net.Uri.parse(url))
                }
                android.util.Log.d("MediaPlaybackService", "Starting prepareAsync()")
                prepareAsync()
                setOnPreparedListener {
                    android.util.Log.d("MediaPlaybackService", "MediaPlayer prepared successfully for URL: $url")
                    android.util.Log.d("MediaPlaybackService", "Duration: ${duration}ms")
                    callback?.invoke(true)
                    // Auto-start if play was requested while preparing
                    if (shouldStartWhenPrepared) {
                        android.util.Log.d("MediaPlaybackService", "Auto-starting playback as requested")
                        shouldStartWhenPrepared = false
                        start()
                        startForegroundService()
                        startProgressUpdates()
                    }
                }
                setOnCompletionListener {
                    android.util.Log.d("MediaPlaybackService", "Chapter completed, moving to next")
                    nextChapter()
                }
                setOnErrorListener { mp, what, extra ->
                    android.util.Log.e("MediaPlaybackService", "MediaPlayer error - what: $what, extra: $extra")
                    android.util.Log.e("MediaPlaybackService", "Failed URL: $url")
                    
                    // More detailed error handling - don't auto-skip on first error
                    when (what) {
                        MediaPlayer.MEDIA_ERROR_UNSUPPORTED -> {
                            android.util.Log.e("MediaPlaybackService", "Unsupported media format for URL: $url")
                        }
                        MediaPlayer.MEDIA_ERROR_IO -> {
                            android.util.Log.e("MediaPlaybackService", "IO error - network issue or invalid URL: $url")
                        }
                        MediaPlayer.MEDIA_ERROR_MALFORMED -> {
                            android.util.Log.e("MediaPlaybackService", "Malformed media data: $url")
                        }
                        MediaPlayer.MEDIA_ERROR_TIMED_OUT -> {
                            android.util.Log.e("MediaPlaybackService", "Network timeout: $url")
                        }
                        else -> {
                            android.util.Log.e("MediaPlaybackService", "Unknown media error: $what, extra: $extra")
                        }
                    }
                    
                    // Notify callback of failure
                    callback?.invoke(false)
                    // Return false to let the system handle the error (don't auto-skip)
                    false
                }
                setOnInfoListener { mp, what, extra ->
                    when (what) {
                        MediaPlayer.MEDIA_INFO_BUFFERING_START -> {
                            android.util.Log.d("MediaPlaybackService", "Buffering started")
                        }
                        MediaPlayer.MEDIA_INFO_BUFFERING_END -> {
                            android.util.Log.d("MediaPlaybackService", "Buffering ended")
                        }
                    }
                    false
                }
            } catch (e: Exception) {
                android.util.Log.e("MediaPlaybackService", "Exception loading audio from URL: $url", e)
                e.printStackTrace()
                callback?.invoke(false)
            }
        }
    }
    
    fun play() {
        android.util.Log.d("MediaPlaybackService", "play() called")
        mediaPlayer?.let { player ->
            android.util.Log.d("MediaPlaybackService", "MediaPlayer state - isPlaying: ${player.isPlaying}")
            try {
                // Check if MediaPlayer is prepared before starting
                val duration = try { player.duration } catch (e: Exception) { -1 }
                android.util.Log.d("MediaPlaybackService", "MediaPlayer duration: $duration")
                
                if (duration > 0) {
                    player.start()
                    android.util.Log.d("MediaPlaybackService", "MediaPlayer started successfully")
                    startForegroundService()
                    startProgressUpdates()
                } else {
                    android.util.Log.d("MediaPlaybackService", "MediaPlayer not ready, setting shouldStartWhenPrepared = true")
                    shouldStartWhenPrepared = true
                }
            } catch (e: Exception) {
                android.util.Log.e("MediaPlaybackService", "Error starting MediaPlayer", e)
                android.util.Log.d("MediaPlaybackService", "Setting shouldStartWhenPrepared = true due to error")
                shouldStartWhenPrepared = true
            }
        } ?: android.util.Log.w("MediaPlaybackService", "MediaPlayer is null, cannot play")
    }
    
    fun pause() {
        mediaPlayer?.pause()
        stopProgressUpdates()
        updateNotification()
    }
    
    fun stop() {
        mediaPlayer?.stop()
        stopProgressUpdates()
        stopForeground(true)
        stopSelf()
    }
    
    fun seekTo(position: Long) {
        mediaPlayer?.seekTo(position.toInt())
    }
    
    fun seekBy(milliseconds: Long) {
        mediaPlayer?.let { player ->
            val newPosition = player.currentPosition + milliseconds.toInt()
            val maxPosition = player.duration
            val seekPosition = newPosition.coerceIn(0, maxPosition)
            player.seekTo(seekPosition)
        }
    }
    
    fun setPlaybackSpeed(speed: Float) {
        // Note: This requires API 23+
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
            mediaPlayer?.playbackParams = mediaPlayer?.playbackParams?.setSpeed(speed) ?: return
        }
    }
    
    fun nextChapter() {
        currentAudiobook?.let { audiobook ->
            if (currentChapter < audiobook.chaptersList.size - 1) {
                loadChapter(currentChapter + 1)
            }
        }
    }
    
    fun previousChapter() {
        if (currentChapter > 0) {
            loadChapter(currentChapter - 1)
        }
    }
    
    fun getCurrentPosition(): Int {
        return mediaPlayer?.currentPosition ?: 0
    }
    
    fun getDuration(): Int {
        return mediaPlayer?.duration ?: 0
    }
    
    fun isPlaying(): Boolean {
        return mediaPlayer?.isPlaying ?: false
    }
    
    fun setVolume(volume: Float) {
        mediaPlayer?.setVolume(volume, volume)
    }
    
    fun mute() {
        mediaPlayer?.setVolume(0f, 0f)
    }
    
    fun unmute() {
        mediaPlayer?.setVolume(1f, 1f)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Audiobook Playback",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Audiobook playback controls"
                setShowBadge(false)
            }
            notificationManager?.createNotificationChannel(channel)
        }
    }
    
    private fun startForegroundService() {
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
    }
    
    private fun updateNotification() {
        val notification = createNotification()
        notificationManager?.notify(NOTIFICATION_ID, notification)
    }
    
    private fun createNotification(): Notification {
        val intent = Intent(this, PlayerActivity::class.java).apply {
            currentAudiobook?.let { putExtra("audiobook", it) }
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val isPlaying = isPlaying()
        val playPauseAction = if (isPlaying) {
            NotificationCompat.Action(
                R.drawable.ic_pause,
                "Pause",
                createMediaActionPendingIntent("pause")
            )
        } else {
            NotificationCompat.Action(
                R.drawable.ic_play,
                "Play",
                createMediaActionPendingIntent("play")
            )
        }
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(currentAudiobook?.title ?: "Audiobook")
            .setContentText("Chapter ${currentChapter + 1}")
            .setSmallIcon(R.drawable.ic_play)
            .setContentIntent(pendingIntent)
            .addAction(
                NotificationCompat.Action(
                    R.drawable.ic_skip_previous,
                    "Previous",
                    createMediaActionPendingIntent("previous")
                )
            )
            .addAction(playPauseAction)
            .addAction(
                NotificationCompat.Action(
                    R.drawable.ic_skip_next,
                    "Next",
                    createMediaActionPendingIntent("next")
                )
            )
            .setStyle(androidx.media.app.NotificationCompat.MediaStyle())
            .setOngoing(isPlaying)
            .build()
    }
    
    private fun createMediaActionPendingIntent(action: String): PendingIntent {
        val intent = Intent(this, MediaPlaybackService::class.java).apply {
            putExtra("action", action)
        }
        return PendingIntent.getService(
            this, action.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        intent?.getStringExtra("action")?.let { action ->
            when (action) {
                "play" -> play()
                "pause" -> pause()
                "next" -> nextChapter()
                "previous" -> previousChapter()
            }
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        stopProgressUpdates()
        mediaPlayer?.release()
        mediaPlayer = null
        mediaSession?.release()
        progressUpdateHandler = null
        progressCallback = null
    }
}