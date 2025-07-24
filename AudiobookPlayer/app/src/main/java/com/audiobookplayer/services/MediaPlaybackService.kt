package com.audiobookplayer.services

import android.app.Service
import android.content.Intent
import android.media.MediaPlayer
import android.os.Binder
import android.os.IBinder
import com.audiobookplayer.models.Audiobook
import com.audiobookplayer.utils.FileManager
import java.io.File

class MediaPlaybackService : Service() {
    
    private val binder = LocalBinder()
    private var mediaPlayer: MediaPlayer? = null
    private lateinit var fileManager: FileManager
    private var currentAudiobook: Audiobook? = null
    private var currentChapter = 0
    
    inner class LocalBinder : Binder() {
        fun getService(): MediaPlaybackService = this@MediaPlaybackService
    }

    override fun onCreate() {
        super.onCreate()
        fileManager = FileManager(this)
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
    }
    
    fun pause() {
        mediaPlayer?.pause()
    }
    
    fun stop() {
        mediaPlayer?.stop()
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

    override fun onDestroy() {
        super.onDestroy()
        mediaPlayer?.release()
        mediaPlayer = null
    }
}