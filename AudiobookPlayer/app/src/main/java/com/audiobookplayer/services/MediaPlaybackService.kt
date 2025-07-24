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
    }

    override fun onBind(intent: Intent): IBinder {
        return binder
    }

    fun loadAudiobook(audiobook: Audiobook) {
        currentAudiobook = audiobook
        currentChapter = audiobook.currentChapter
        loadChapter(currentChapter)
    }
    
    fun loadChapter(chapterIndex: Int) {
        currentAudiobook?.let { audiobook ->
            val chapterFiles = fileManager.getChapterFiles(audiobook.id)
            if (chapterIndex >= 0 && chapterIndex < chapterFiles.size) {
                val chapterFile = chapterFiles[chapterIndex]
                loadAudioFile(chapterFile)
                currentChapter = chapterIndex
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
    
    fun play() {
        mediaPlayer?.start()
        startForegroundService()
    }
    
    fun pause() {
        mediaPlayer?.pause()
        updateNotification()
    }
    
    fun stop() {
        mediaPlayer?.stop()
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
            if (currentChapter < audiobook.totalChapters - 1) {
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
        mediaPlayer?.release()
        mediaPlayer = null
        mediaSession?.release()
    }
}