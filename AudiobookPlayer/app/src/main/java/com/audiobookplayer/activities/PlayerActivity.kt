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
import com.audiobookplayer.R
import com.audiobookplayer.models.Audiobook
import com.audiobookplayer.services.MediaPlaybackService
import com.audiobookplayer.utils.FileManager
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

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as MediaPlaybackService.LocalBinder
            mediaService = binder.getService()
            isBound = true
            
            // Initialize player with audiobook
            mediaService?.loadAudiobook(audiobook)
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
        btnPlayPause.setOnClickListener {
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
        
        btnVolume.setOnClickListener {
            toggleMute()
        }
        
        btnSleepTimer.setOnClickListener {
            // TODO: Show sleep timer dialog
        }
        
        btnBookmark.setOnClickListener {
            // TODO: Add bookmark
        }
        
        seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                if (fromUser) {
                    mediaService?.seekTo(progress.toLong())
                }
            }
            
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
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
        tvChapterInfo.text = getString(
            R.string.chapter_format, 
            currentChapter + 1, 
            audiobook.chapters
        )
    }
    
    private fun updatePlayPauseButton() {
        val iconRes = if (isPlaying) R.drawable.ic_pause else R.drawable.ic_play
        btnPlayPause.setImageDrawable(ContextCompat.getDrawable(this, iconRes))
    }
    
    private fun updateSpeedButton() {
        btnSpeed.text = getString(R.string.speed_format, playbackSpeed)
    }
    
    private fun updateVolumeButton() {
        val iconRes = if (isMuted) R.drawable.ic_volume_off else R.drawable.ic_volume_up
        btnVolume.setImageDrawable(ContextCompat.getDrawable(this, iconRes))
    }

    private fun togglePlayPause() {
        if (isPlaying) {
            mediaService?.pause()
        } else {
            mediaService?.play()
        }
        isPlaying = !isPlaying
        updatePlayPauseButton()
    }
    
    private fun previousChapter() {
        if (currentChapter > 0) {
            currentChapter--
            mediaService?.loadChapter(currentChapter)
            updateChapterInfo()
        }
    }
    
    private fun nextChapter() {
        if (currentChapter < audiobook.chapters - 1) {
            currentChapter++
            mediaService?.loadChapter(currentChapter)
            updateChapterInfo()
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
        if (isMuted) {
            audioManager.setStreamMute(AudioManager.STREAM_MUSIC, true)
        } else {
            audioManager.setStreamMute(AudioManager.STREAM_MUSIC, false)
        }
        updateVolumeButton()
    }

    override fun onDestroy() {
        super.onDestroy()
        if (isBound) {
            unbindService(serviceConnection)
            isBound = false
        }
    }
}