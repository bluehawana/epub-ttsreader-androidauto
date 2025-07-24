package com.audiobookplayer.activities

import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.audiobookplayer.R
import com.audiobookplayer.adapters.AudiobookAdapter
import com.audiobookplayer.models.Audiobook
import com.audiobookplayer.services.ApiConfig
import com.audiobookplayer.utils.FileManager
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.textfield.TextInputEditText
import androidx.recyclerview.widget.RecyclerView
import android.widget.TextView
import android.widget.LinearLayout
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    
    private lateinit var etUserId: TextInputEditText
    private lateinit var btnSync: MaterialButton
    private lateinit var tvSyncStatus: TextView
    private lateinit var rvAudiobooks: RecyclerView
    private lateinit var emptyState: LinearLayout
    private lateinit var progressLoading: CircularProgressIndicator
    
    private lateinit var audiobookAdapter: AudiobookAdapter
    private lateinit var fileManager: FileManager
    private lateinit var prefs: SharedPreferences
    
    private var currentUserId: String? = null
    private val audiobooks = mutableListOf<Audiobook>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        initViews()
        initServices()
        setupRecyclerView()
        setupClickListeners()
        loadSavedUserId()
    }

    private fun initViews() {
        etUserId = findViewById(R.id.etUserId)
        btnSync = findViewById(R.id.btnSync)
        tvSyncStatus = findViewById(R.id.tvSyncStatus)
        rvAudiobooks = findViewById(R.id.rvAudiobooks)
        emptyState = findViewById(R.id.emptyState)
        progressLoading = findViewById(R.id.progressLoading)
    }
    
    private fun initServices() {
        fileManager = FileManager(this)
        prefs = getSharedPreferences("audiobook_prefs", MODE_PRIVATE)
    }

    private fun setupRecyclerView() {
        audiobookAdapter = AudiobookAdapter(
            audiobooks = audiobooks,
            onPlayClick = { audiobook ->
                openPlayer(audiobook)
            },
            onDownloadClick = { audiobook ->
                downloadAudiobook(audiobook)
            },
            onDeleteClick = { audiobook ->
                deleteAudiobook(audiobook)
            }
        )
        
        rvAudiobooks.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = audiobookAdapter
        }
    }

    private fun setupClickListeners() {
        btnSync.setOnClickListener {
            val userId = etUserId.text.toString().trim()
            if (userId.isNotEmpty()) {
                currentUserId = userId
                saveUserId(userId)
                syncAudiobooks(userId)
            } else {
                Toast.makeText(this, "Please enter your User ID", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun loadSavedUserId() {
        val savedUserId = prefs.getString("user_id", "")
        if (!savedUserId.isNullOrEmpty()) {
            etUserId.setText(savedUserId)
            currentUserId = savedUserId
            // Auto-sync on app start
            syncAudiobooks(savedUserId)
        }
    }

    private fun saveUserId(userId: String) {
        prefs.edit().putString("user_id", userId).apply()
    }

    private fun syncAudiobooks(userId: String) {
        lifecycleScope.launch {
            try {
                showLoading(true)
                tvSyncStatus.text = "Syncing audiobooks..."
                
                val response = ApiConfig.apiService.getUserAudiobooks(userId)
                
                if (response.isSuccessful && response.body() != null) {
                    val audiobookResponse = response.body()!!
                    audiobooks.clear()
                    audiobooks.addAll(audiobookResponse.audiobooks)
                    
                    // Check which audiobooks are already downloaded
                    audiobooks.forEach { audiobook ->
                        audiobook.isDownloaded = fileManager.isAudiobookDownloaded(audiobook.id)
                        if (audiobook.isDownloaded) {
                            audiobook.localPath = fileManager.getAudiobookPath(audiobook.id)
                        }
                    }
                    
                    audiobookAdapter.updateAudiobooks(audiobooks)
                    updateEmptyState()
                    
                    tvSyncStatus.text = if (audiobooks.isEmpty()) {
                        "No audiobooks found. Send EPUB files to your Telegram bot."
                    } else {
                        "Found ${audiobooks.size} audiobook(s)"
                    }
                    
                } else {
                    tvSyncStatus.text = "Sync failed: ${response.message()}"
                    Toast.makeText(this@MainActivity, "Failed to sync audiobooks", Toast.LENGTH_SHORT).show()
                }
                
            } catch (e: Exception) {
                tvSyncStatus.text = "Sync error: ${e.message}"
                Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                showLoading(false)
            }
        }
    }

    private fun downloadAudiobook(audiobook: Audiobook) {
        lifecycleScope.launch {
            try {
                Toast.makeText(this@MainActivity, "Downloading ${audiobook.title}...", Toast.LENGTH_SHORT).show()
                
                // Get detailed audiobook info with chapter URLs
                val detailResponse = ApiConfig.apiService.getAudiobookDetails(audiobook.id)
                
                if (detailResponse.isSuccessful && detailResponse.body() != null) {
                    val details = detailResponse.body()!!
                    
                    // Download each chapter
                    val success = fileManager.downloadAudiobook(audiobook.id, audiobook.title, details.chapters)
                    
                    if (success) {
                        audiobook.isDownloaded = true
                        audiobook.localPath = fileManager.getAudiobookPath(audiobook.id)
                        audiobookAdapter.updateAudiobooks(audiobooks)
                        Toast.makeText(this@MainActivity, "Downloaded ${audiobook.title}", Toast.LENGTH_SHORT).show()
                    } else {
                        Toast.makeText(this@MainActivity, "Download failed", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this@MainActivity, "Failed to get audiobook details", Toast.LENGTH_SHORT).show()
                }
                
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Download error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun deleteAudiobook(audiobook: Audiobook) {
        val success = fileManager.deleteAudiobook(audiobook.id)
        if (success) {
            audiobook.isDownloaded = false
            audiobook.localPath = null
            audiobookAdapter.updateAudiobooks(audiobooks)
            Toast.makeText(this, "Deleted ${audiobook.title}", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(this, "Failed to delete audiobook", Toast.LENGTH_SHORT).show()
        }
    }

    private fun openPlayer(audiobook: Audiobook) {
        val intent = Intent(this, PlayerActivity::class.java)
        intent.putExtra("audiobook", audiobook)
        startActivity(intent)
    }

    private fun showLoading(show: Boolean) {
        progressLoading.visibility = if (show) View.VISIBLE else View.GONE
        btnSync.isEnabled = !show
    }

    private fun updateEmptyState() {
        emptyState.visibility = if (audiobooks.isEmpty()) View.VISIBLE else View.GONE
        rvAudiobooks.visibility = if (audiobooks.isEmpty()) View.GONE else View.VISIBLE
    }
}