package com.audiobookplayer.activities

import android.media.MediaPlayer
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.audiobookplayer.R

class DebugActivity : AppCompatActivity() {
    
    private lateinit var etUrl: EditText
    private lateinit var btnTest: Button
    private lateinit var btnPlay: Button
    private lateinit var btnStop: Button
    private lateinit var tvResult: TextView
    private var mediaPlayer: MediaPlayer? = null
    private var isPrepared = false
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_debug)
        
        initViews()
        setupClickListeners()
    }
    
    private fun initViews() {
        etUrl = findViewById(R.id.etUrl)
        btnTest = findViewById(R.id.btnTest)
        btnPlay = findViewById(R.id.btnPlay)
        btnStop = findViewById(R.id.btnStop)
        tvResult = findViewById(R.id.tvResult)
        
        // Pre-fill with a test streaming URL
        etUrl.setText("https://epub-audiobook-service-ab00bb696e09.herokuapp.com/api/stream/1141127507/3da9b6f3-3eae-4a06-9687-9e7743817194/chapter_1.mp3")
        
        // Initially disable play/stop buttons
        btnPlay.isEnabled = false
        btnStop.isEnabled = false
    }
    
    private fun setupClickListeners() {
        btnTest.setOnClickListener {
            val url = etUrl.text.toString().trim()
            if (url.isNotEmpty()) {
                testUrl(url)
            }
        }
        
        btnPlay.setOnClickListener {
            if (isPrepared && mediaPlayer != null) {
                try {
                    mediaPlayer?.start()
                    appendResult("▶️ Started playback")
                    btnPlay.isEnabled = false
                    btnStop.isEnabled = true
                } catch (e: Exception) {
                    appendResult("❌ Play error: ${e.message}")
                }
            }
        }
        
        btnStop.setOnClickListener {
            try {
                mediaPlayer?.pause()
                appendResult("⏸️ Stopped playback")
                btnPlay.isEnabled = true
                btnStop.isEnabled = false
            } catch (e: Exception) {
                appendResult("❌ Stop error: ${e.message}")
            }
        }
    }
    
    private fun testUrl(url: String) {
        tvResult.text = "Testing URL: $url\n\n"
        appendResult("Starting test...")
        
        // Reset state
        isPrepared = false
        btnPlay.isEnabled = false
        btnStop.isEnabled = false
        
        mediaPlayer?.release()
        mediaPlayer = MediaPlayer().apply {
            try {
                appendResult("Setting data source...")
                
                // Use simple string-based setDataSource for HTTP URLs
                if (url.startsWith("http")) {
                    setDataSource(url)
                    appendResult("HTTP data source set, preparing...")
                } else {
                    setDataSource(this@DebugActivity, android.net.Uri.parse(url))
                    appendResult("URI data source set, preparing...")
                }
                
                setOnPreparedListener {
                    isPrepared = true
                    appendResult("✅ MediaPlayer prepared successfully!")
                    appendResult("Duration: ${duration}ms (${duration/1000}s)")
                    appendResult("Ready to play - click Play button")
                    runOnUiThread {
                        btnPlay.isEnabled = true
                    }
                }
                
                setOnErrorListener { _, what, extra ->
                    appendResult("❌ MediaPlayer error:")
                    appendResult("What: $what")
                    appendResult("Extra: $extra")
                    
                    when (what) {
                        MediaPlayer.MEDIA_ERROR_UNSUPPORTED -> appendResult("Error: Unsupported media format")
                        MediaPlayer.MEDIA_ERROR_IO -> appendResult("Error: IO/Network error")
                        MediaPlayer.MEDIA_ERROR_MALFORMED -> appendResult("Error: Malformed media")
                        MediaPlayer.MEDIA_ERROR_TIMED_OUT -> appendResult("Error: Network timeout")
                        else -> appendResult("Error: Unknown error")
                    }
                    false
                }
                
                setOnInfoListener { _, what, extra ->
                    when (what) {
                        MediaPlayer.MEDIA_INFO_BUFFERING_START -> appendResult("Buffering started...")
                        MediaPlayer.MEDIA_INFO_BUFFERING_END -> appendResult("Buffering ended")
                    }
                    false
                }
                
                prepareAsync()
                
            } catch (e: Exception) {
                appendResult("❌ Exception: ${e.message}")
                e.printStackTrace()
            }
        }
    }
    
    private fun appendResult(message: String) {
        runOnUiThread {
            tvResult.append("$message\n")
        }
        android.util.Log.d("DebugActivity", message)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        mediaPlayer?.release()
    }
}