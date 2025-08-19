package com.audiobookplayer.activities

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.media.AudioManager
import android.os.Bundle
import android.os.IBinder
import android.widget.ImageButton
import android.widget.SeekBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.audiobookplayer.R
import com.audiobookplayer.models.Audiobook
import com.audiobookplayer.services.ApiConfig
import com.audiobookplayer.services.MediaPlaybackService
import com.audiobookplayer.utils.FileManager
import kotlinx.coroutines.launch
import com.google.android.material.button.MaterialButton
import com.google.android.material.floatingactionbutton.FloatingActionButton

class PlayerActivity : AppCompatActivity() {
    
    private lateinit var audiobook: Audiobook
    private lateinit var fileManager: FileManager
    private lateinit var audioManager: AudioManager
    
    // UI Components
    private lateinit var tvBookTitle: TextView
    private lateinit var tvAuthor: TextView
    private lateinit var tvChapterInfo: TextView
    private lateinit var tvCurrentTime: TextView
    private lateinit var tvTotalTime: TextView
    private lateinit var seekBar: SeekBar
    private lateinit var btnPlayPause: FloatingActionButton
    private lateinit var btnPreviousChapter: ImageButton
    private lateinit var btnNextChapter: ImageButton
    private lateinit var btnRewind: ImageButton
    private lateinit var btnForward: ImageButton
    private lateinit var btnSpeed: MaterialButton
    private lateinit var btnVolume: ImageButton
    private lateinit var btnSleepTimer: ImageButton
    private lateinit var btnBookmark: ImageButton
    
    // Media Service
    private var mediaService: MediaPlaybackService? = null
    private var isBound = false
    
    private var currentChapter = 0
    private var isPlaying = false
    private var playbackSpeed = 1.0f
    private var isMuted = false
    private var currentDuration = 0
    private var currentPosition = 0

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as MediaPlaybackService.LocalBinder
            mediaService = binder.getService()
            isBound = true
            
            // Initialize player with audiobook
            mediaService?.loadAudiobook(audiobook)
            
            // Set up progress callback
            mediaService?.setProgressCallback { position, duration ->
                runOnUiThread {
                    updateProgress(position, duration)
                }
            }
            
            updateUI()
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            mediaService = null
            isBound = false
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_player)
        
        // Get audiobook from intent
        audiobook = intent.getSerializableExtra("audiobook") as Audiobook
        
        // Debug logging and chapter loading fix
        android.util.Log.d("PlayerActivity", "Received audiobook: ${audiobook.title}")
        android.util.Log.d("PlayerActivity", "Chapters count: ${audiobook.chapters}")
        android.util.Log.d("PlayerActivity", "ChaptersList size: ${audiobook.chaptersList.size}")
        
        // If chaptersList is empty, reload chapter details
        if (audiobook.chaptersList.isEmpty()) {
            android.util.Log.d("PlayerActivity", "ChaptersList is empty, reloading from API...")
            loadChapterDetails()
        }
        
        initViews()
        initServices()
        setupClickListeners()
        updateUI()
        
        // Bind to media service
        bindMediaService()
    }

    private fun initViews() {
        tvBookTitle = findViewById(R.id.tvBookTitle)
        tvAuthor = findViewById(R.id.tvAuthor)
        tvChapterInfo = findViewById(R.id.tvChapterInfo)
        tvCurrentTime = findViewById(R.id.tvCurrentTime)
        tvTotalTime = findViewById(R.id.tvTotalTime)
        seekBar = findViewById(R.id.seekBar)
        btnPlayPause = findViewById(R.id.btnPlayPause)
        btnPreviousChapter = findViewById(R.id.btnPreviousChapter)
        btnNextChapter = findViewById(R.id.btnNextChapter)
        btnRewind = findViewById(R.id.btnRewind)
        btnForward = findViewById(R.id.btnForward)
        btnSpeed = findViewById(R.id.btnSpeed)
        btnVolume = findViewById(R.id.btnVolume)
        btnSleepTimer = findViewById(R.id.btnSleepTimer)
        btnBookmark = findViewById(R.id.btnBookmark)
        
        // Debug logging
        android.util.Log.d("PlayerActivity", "Button references - Volume: $btnVolume, Sleep: $btnSleepTimer, Bookmark: $btnBookmark")
        
        // Setup toolbar
        findViewById<androidx.appcompat.widget.Toolbar>(R.id.toolbar).setNavigationOnClickListener {
            finish()
        }
    }
    
    private fun initServices() {
        fileManager = FileManager(this)
        audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        currentChapter = audiobook.currentChapter
    }

    private fun setupClickListeners() {
        android.util.Log.d("PlayerActivity", "Setting up click listeners...")
        
        btnPlayPause.setOnClickListener {
            android.util.Log.d("PlayerActivity", "Play/Pause button clicked")
            togglePlayPause()
        }
        
        btnPreviousChapter.setOnClickListener {
            previousChapter()
        }
        
        btnNextChapter.setOnClickListener {
            nextChapter()
        }
        
        btnRewind.setOnClickListener {
            seekBy(-30000) // Rewind 30 seconds
        }
        
        btnForward.setOnClickListener {
            seekBy(30000) // Forward 30 seconds
        }
        
        btnSpeed.setOnClickListener {
            cyclePlaybackSpeed()
        }
        
        android.util.Log.d("PlayerActivity", "Setting up volume button listener...")
        btnVolume.setOnClickListener {
            android.util.Log.d("PlayerActivity", "Volume button clicked!")
            android.widget.Toast.makeText(this, "Volume button works!", android.widget.Toast.LENGTH_SHORT).show()
            toggleMute()
        }
        
        android.util.Log.d("PlayerActivity", "Setting up sleep timer button listener...")
        btnSleepTimer.setOnClickListener {
            android.util.Log.d("PlayerActivity", "Sleep timer button clicked!")
            android.widget.Toast.makeText(this, "Sleep timer button works!", android.widget.Toast.LENGTH_SHORT).show()
            showSleepTimerDialog()
        }
        
        android.util.Log.d("PlayerActivity", "Setting up bookmark button listener...")
        btnBookmark.setOnClickListener {
            android.util.Log.d("PlayerActivity", "Bookmark button clicked!")
            android.widget.Toast.makeText(this, "Bookmark button works!", android.widget.Toast.LENGTH_SHORT).show()
            addBookmark()
        }
        
        seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                if (fromUser && currentDuration > 0) {
                    val seekPosition = (progress * currentDuration / 100).toLong()
                    mediaService?.seekTo(seekPosition)
                }
            }
            
            override fun onStartTrackingTouch(seekBar: SeekBar?) {
                // User started dragging, could pause updates temporarily
            }
            
            override fun onStopTrackingTouch(seekBar: SeekBar?) {
                // User finished dragging, resume updates
            }
        })
    }

    private fun bindMediaService() {
        val intent = Intent(this, MediaPlaybackService::class.java)
        bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
    }

    private fun updateUI() {
        tvBookTitle.text = audiobook.title
        tvAuthor.text = audiobook.author ?: "Unknown Author"
        updateChapterInfo()
        updatePlayPauseButton()
        updateSpeedButton()
        updateVolumeButton()
    }
    
    private fun updateChapterInfo() {
        val chapterText = if (audiobook.chaptersList.isNotEmpty() && currentChapter < audiobook.chaptersList.size) {
            val chapter = audiobook.chaptersList[currentChapter]
            val durationText = if (chapter.duration > 0) {
                " • ${formatDuration(chapter.duration * 1000)}" // Convert seconds to milliseconds
            } else {
                ""
            }
            "Chapter ${currentChapter + 1} of ${audiobook.chapters}$durationText"
        } else {
            "Chapter ${currentChapter + 1} of ${audiobook.chapters}"
        }
        tvChapterInfo.text = chapterText
    }
    
    private fun updateProgress(position: Int, duration: Int) {
        currentPosition = position
        currentDuration = duration
        
        // Update time displays
        tvCurrentTime.text = formatDuration(position)
        tvTotalTime.text = formatDuration(duration)
        
        // Update seek bar
        if (duration > 0) {
            val progress = (position * 100 / duration)
            seekBar.progress = progress
        }
    }
    
    private fun formatDuration(milliseconds: Int): String {
        val totalSeconds = milliseconds / 1000
        val minutes = totalSeconds / 60
        val seconds = totalSeconds % 60
        
        return if (minutes >= 60) {
            val hours = minutes / 60
            val remainingMinutes = minutes % 60
            String.format("%d:%02d:%02d", hours, remainingMinutes, seconds)
        } else {
            String.format("%d:%02d", minutes, seconds)
        }
    }
    
    private fun updatePlayPauseButton() {
        val iconRes = if (isPlaying) R.drawable.ic_pause else R.drawable.ic_play
        btnPlayPause.setImageResource(iconRes)
    }
    
    private fun updateSpeedButton() {
        btnSpeed.text = getString(R.string.speed_format, playbackSpeed)
    }
    
    private fun updateVolumeButton() {
        val iconRes = if (isMuted) R.drawable.ic_volume_off else R.drawable.ic_volume_up
        btnVolume.setImageResource(iconRes)
    }

    private fun togglePlayPause() {
        android.util.Log.d("PlayerActivity", "togglePlayPause() called - current isPlaying: $isPlaying")
        android.util.Log.d("PlayerActivity", "MediaService bound: $isBound, service: $mediaService")
        
        if (!isBound || mediaService == null) {
            android.util.Log.w("PlayerActivity", "MediaService not bound or null, cannot toggle playback")
            android.widget.Toast.makeText(this, "Audio player not ready, please wait...", android.widget.Toast.LENGTH_SHORT).show()
            return
        }
        
        try {
            if (isPlaying) {
                android.util.Log.d("PlayerActivity", "Calling mediaService.pause()")
                mediaService?.pause()
            } else {
                android.util.Log.d("PlayerActivity", "Calling mediaService.play()")
                mediaService?.play()
            }
            isPlaying = !isPlaying
            android.util.Log.d("PlayerActivity", "Updated isPlaying to: $isPlaying")
            updatePlayPauseButton()
        } catch (e: Exception) {
            android.util.Log.e("PlayerActivity", "Error toggling playback", e)
            android.widget.Toast.makeText(this, "Playback error: ${e.message}", android.widget.Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun previousChapter() {
        if (currentChapter > 0) {
            val wasPlaying = isPlaying
            currentChapter--
            mediaService?.loadChapter(currentChapter)
            updateChapterInfo()
            // Reset progress display
            updateProgress(0, 0)
            // Resume playback after a short delay if it was playing
            if (wasPlaying) {
                android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                    mediaService?.play()
                }, 1000) // Give MediaPlayer time to prepare
            }
        }
    }
    
    private fun nextChapter() {
        if (currentChapter < audiobook.chapters - 1) {
            val wasPlaying = isPlaying
            currentChapter++
            mediaService?.loadChapter(currentChapter)
            updateChapterInfo()
            // Reset progress display
            updateProgress(0, 0)
            // Resume playback after a short delay if it was playing
            if (wasPlaying) {
                android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                    mediaService?.play()
                }, 1000) // Give MediaPlayer time to prepare
            }
        }
    }
    
    private fun seekBy(milliseconds: Int) {
        mediaService?.seekBy(milliseconds.toLong())
    }
    
    private fun cyclePlaybackSpeed() {
        playbackSpeed = when (playbackSpeed) {
            0.5f -> 0.75f
            0.75f -> 1.0f
            1.0f -> 1.25f
            1.25f -> 1.5f
            1.5f -> 2.0f
            else -> 0.5f
        }
        mediaService?.setPlaybackSpeed(playbackSpeed)
        updateSpeedButton()
    }
    
    private fun toggleMute() {
        isMuted = !isMuted
        
        // Mute the MediaPlayer directly for immediate effect
        if (isMuted) {
            mediaService?.mute()
            android.util.Log.d("PlayerActivity", "MediaPlayer muted")
        } else {
            mediaService?.unmute()
            android.util.Log.d("PlayerActivity", "MediaPlayer unmuted")
        }
        
        updateVolumeButton()
        android.widget.Toast.makeText(this, if (isMuted) "Audio muted" else "Audio unmuted", android.widget.Toast.LENGTH_SHORT).show()
    }

    private fun loadChapterDetails() {
        lifecycleScope.launch {
            try {
                val response = ApiConfig.apiService.getAudiobookDetails(audiobook.id)
                if (response.isSuccessful && response.body() != null) {
                    val details = response.body()!!
                    audiobook.chaptersList = details.chapters
                    android.util.Log.d("PlayerActivity", "Reloaded ${details.chapters.size} chapters")
                    
                    // If service is already bound, reload the audiobook
                    if (isBound) {
                        mediaService?.loadAudiobook(audiobook)
                    }
                } else {
                    android.util.Log.e("PlayerActivity", "Failed to reload chapter details")
                }
            } catch (e: Exception) {
                android.util.Log.e("PlayerActivity", "Error reloading chapters: ${e.message}")
            }
        }
    }

    private fun showSleepTimerDialog() {
        android.util.Log.d("PlayerActivity", "showSleepTimerDialog() called")
        val options = arrayOf("15 minutes", "30 minutes", "45 minutes", "1 hour", "Cancel")
        val builder = androidx.appcompat.app.AlertDialog.Builder(this)
        builder.setTitle("Sleep Timer")
            .setItems(options) { dialog, which ->
                android.util.Log.d("PlayerActivity", "Sleep timer option selected: $which")
                when (which) {
                    0 -> setSleepTimer(15 * 60 * 1000L) // 15 minutes
                    1 -> setSleepTimer(30 * 60 * 1000L) // 30 minutes  
                    2 -> setSleepTimer(45 * 60 * 1000L) // 45 minutes
                    3 -> setSleepTimer(60 * 60 * 1000L) // 1 hour
                    4 -> {
                        android.util.Log.d("PlayerActivity", "Sleep timer cancelled")
                        dialog.dismiss()
                    }
                }
            }
        try {
            val dialog = builder.create()
            dialog.show()
            android.util.Log.d("PlayerActivity", "Sleep timer dialog shown successfully")
        } catch (e: Exception) {
            android.util.Log.e("PlayerActivity", "Error showing sleep timer dialog", e)
            android.widget.Toast.makeText(this, "Error showing sleep timer: ${e.message}", android.widget.Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun setSleepTimer(delayMillis: Long) {
        val minutes = delayMillis / 60000
        android.widget.Toast.makeText(this, "Sleep timer set for $minutes minutes", android.widget.Toast.LENGTH_LONG).show()
        android.util.Log.d("PlayerActivity", "Sleep timer set for $minutes minutes ($delayMillis ms)")
        
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
            android.util.Log.d("PlayerActivity", "Sleep timer expired - pausing playback")
            mediaService?.pause()
            isPlaying = false
            updatePlayPauseButton()
            android.widget.Toast.makeText(this, "Sleep timer expired - playback paused", android.widget.Toast.LENGTH_LONG).show()
        }, delayMillis)
    }
    
    private fun addBookmark() {
        android.util.Log.d("PlayerActivity", "addBookmark() called")
        try {
            val currentPosition = (mediaService?.getCurrentPosition() ?: 0).toLong()
            val bookmarkText = "Chapter ${currentChapter + 1} at ${formatTime(currentPosition)}"
            
            // Save bookmark to SharedPreferences
            val bookmarks = getSharedPreferences("audiobook_prefs", Context.MODE_PRIVATE)
            val existingBookmarks = bookmarks.getString("bookmarks_${audiobook.id}", "") ?: ""
            val newBookmarks = if (existingBookmarks.isEmpty()) {
                bookmarkText
            } else {
                "$existingBookmarks\n$bookmarkText"
            }
            
            bookmarks.edit()
                .putString("bookmarks_${audiobook.id}", newBookmarks)
                .apply()
            
            // Update button appearance to show bookmark was saved
            btnBookmark.setImageResource(R.drawable.ic_bookmark) // Filled bookmark
            btnBookmark.setColorFilter(ContextCompat.getColor(this, android.R.color.holo_orange_dark))
            
            // Reset button appearance after 2 seconds
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                btnBookmark.setImageResource(R.drawable.ic_bookmark_border) // Empty bookmark
                btnBookmark.clearColorFilter()
            }, 2000)
            
            android.widget.Toast.makeText(this, "Bookmark saved: $bookmarkText", android.widget.Toast.LENGTH_SHORT).show()
            android.util.Log.d("PlayerActivity", "Bookmark saved: $bookmarkText")
        } catch (e: Exception) {
            android.util.Log.e("PlayerActivity", "Error adding bookmark", e)
            android.widget.Toast.makeText(this, "Error saving bookmark: ${e.message}", android.widget.Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun formatTime(milliseconds: Long): String {
        val minutes = (milliseconds / 1000) / 60
        val seconds = (milliseconds / 1000) % 60
        return String.format("%02d:%02d", minutes, seconds)
    }

    override fun onPause() {
        super.onPause()
        // Save current playback position for Netflix-style resume
        savePlaybackPosition()
    }
    
    override fun onResume() {
        super.onResume()
        // Restore playback position when returning to the app
        restorePlaybackPosition()
    }
    
    private fun savePlaybackPosition() {
        try {
            val currentPosition = mediaService?.getCurrentPosition() ?: 0
            val prefs = getSharedPreferences("audiobook_prefs", Context.MODE_PRIVATE)
            prefs.edit()
                .putInt("last_position_${audiobook.id}", currentPosition)
                .putInt("last_chapter_${audiobook.id}", currentChapter)
                .putLong("last_played_${audiobook.id}", System.currentTimeMillis())
                .apply()
            
            android.util.Log.d("PlayerActivity", "Saved playback position: chapter=$currentChapter, position=${currentPosition}ms")
        } catch (e: Exception) {
            android.util.Log.e("PlayerActivity", "Error saving playback position", e)
        }
    }
    
    private fun restorePlaybackPosition() {
        try {
            // Skip restore during initial setup to prevent ANR
            if (!isBound || mediaService == null) {
                android.util.Log.d("PlayerActivity", "Skipping restore - service not ready")
                return
            }
            
            val prefs = getSharedPreferences("audiobook_prefs", Context.MODE_PRIVATE)
            val savedPosition = prefs.getInt("last_position_${audiobook.id}", 0)
            val savedChapter = prefs.getInt("last_chapter_${audiobook.id}", 0)
            val lastPlayed = prefs.getLong("last_played_${audiobook.id}", 0)
            
            // Only restore if played within last 7 days and position is significant (>30 seconds)
            if (savedPosition > 30000 && System.currentTimeMillis() - lastPlayed < 7 * 24 * 60 * 60 * 1000) {
                android.util.Log.d("PlayerActivity", "Restoring playback position: chapter=$savedChapter, position=${savedPosition}ms")
                
                // Restore chapter if different and valid
                if (savedChapter != currentChapter && savedChapter >= 0 && savedChapter < audiobook.chapters) {
                    currentChapter = savedChapter
                    updateChapterInfo()
                    // Don't reload chapter immediately to prevent blocking
                }
                
                // Show restore message without actually seeking to prevent ANR
                android.widget.Toast.makeText(this, "Resume available from ${formatTime(savedPosition.toLong())}", android.widget.Toast.LENGTH_SHORT).show()
            }
        } catch (e: Exception) {
            android.util.Log.e("PlayerActivity", "Error restoring playback position", e)
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        // Save position before destroying
        savePlaybackPosition()
        
        if (isBound) {
            unbindService(serviceConnection)
            isBound = false
        }
    }
}