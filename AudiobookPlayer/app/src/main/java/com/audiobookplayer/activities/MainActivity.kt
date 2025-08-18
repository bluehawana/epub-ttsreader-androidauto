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
import com.audiobookplayer.models.Chapter
import com.audiobookplayer.models.ProcessingStatus
import com.audiobookplayer.services.ApiConfig
import com.audiobookplayer.utils.FileManager
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.textfield.TextInputEditText
import androidx.recyclerview.widget.RecyclerView
import android.widget.TextView
import android.widget.LinearLayout
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.withContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import androidx.cardview.widget.CardView
import com.google.android.material.progressindicator.LinearProgressIndicator
import android.util.Log
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.content.Context

class MainActivity : AppCompatActivity() {
    
    private lateinit var etUserId: TextInputEditText
    private lateinit var btnSync: MaterialButton
    private lateinit var btnProcessEpubs: MaterialButton
    private lateinit var tvSyncStatus: TextView
    private lateinit var rvAudiobooks: RecyclerView
    private lateinit var emptyState: LinearLayout
    private lateinit var progressLoading: CircularProgressIndicator
    
    // Processing status views
    private lateinit var processingStatusCard: CardView
    private lateinit var tvProcessingTitle: TextView
    private lateinit var tvProcessingDetails: TextView
    private lateinit var progressProcessing: LinearProgressIndicator
    
    private lateinit var audiobookAdapter: AudiobookAdapter
    private lateinit var fileManager: FileManager
    private lateinit var prefs: SharedPreferences
    
    private var currentUserId: String? = null
    private val audiobooks = mutableListOf<Audiobook>()
    
    // QR Scanner request code
    companion object {
        private const val QR_SCANNER_REQUEST_CODE = 1001
    }

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
        btnProcessEpubs = findViewById(R.id.btnProcessEpubs)
        tvSyncStatus = findViewById(R.id.tvSyncStatus)
        rvAudiobooks = findViewById(R.id.rvAudiobooks)
        emptyState = findViewById(R.id.emptyState)
        progressLoading = findViewById(R.id.progressLoading)
        
        // Processing status views
        processingStatusCard = findViewById(R.id.processingStatusCard)
        tvProcessingTitle = findViewById(R.id.tvProcessingTitle)
        tvProcessingDetails = findViewById(R.id.tvProcessingDetails)
        progressProcessing = findViewById(R.id.progressProcessing)
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
            },
            onDeleteFromServerClick = { audiobook ->
                deleteAudiobookFromServer(audiobook)
            },
            onDeleteDuplicatesClick = { audiobook ->
                deleteAllCopiesOfBook(audiobook)
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
        
        btnProcessEpubs.setOnClickListener {
            processAllEpubs()
        }
        
        // Add network test button (temporary)
        btnProcessEpubs.setOnLongClickListener {
            testNetworkConnectivity()
            true
        }
        
        // Add debug menu (long press on sync button)
        btnSync.setOnLongClickListener {
            val intent = Intent(this, DebugActivity::class.java)
            startActivity(intent)
            true
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

    private fun isNetworkAvailable(): Boolean {
        val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val networkCapabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return networkCapabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }
    
    private fun testNetworkConnectivity() {
        lifecycleScope.launch {
            try {
                Log.d("MainActivity", "=== Network Connectivity Test ===")
                Log.d("MainActivity", "Network available: ${isNetworkAvailable()}")
                
                Toast.makeText(this@MainActivity, "Testing network connectivity...", Toast.LENGTH_SHORT).show()
                
                // Test with Google DNS first
                val googleDnsTest = withTimeoutOrNull(5000) {
                    withContext(Dispatchers.IO) {
                        try {
                            val url = java.net.URL("https://8.8.8.8/")
                            val connection = url.openConnection() as java.net.HttpURLConnection
                            connection.requestMethod = "GET"
                            connection.connectTimeout = 3000
                            connection.readTimeout = 3000
                            connection.responseCode == 200
                        } catch (e: Exception) {
                            Log.e("MainActivity", "Google DNS test failed: ${e.message}")
                            false
                        }
                    }
                }
                
                // Test hostname resolution
                val hostnameTest = withTimeoutOrNull(5000) {
                    withContext(Dispatchers.IO) {
                        try {
                            java.net.InetAddress.getByName("epub-audiobook-service-ab00bb696e09.herokuapp.com")
                            true
                        } catch (e: Exception) {
                            Log.e("MainActivity", "Hostname resolution failed: ${e.message}")
                            false
                        }
                    }
                }
                
                // Test direct IP connection
                val ipTest = withTimeoutOrNull(5000) {
                    withContext(Dispatchers.IO) {
                        try {
                            val url = java.net.URL("https://18.208.60.216/health")
                            val connection = url.openConnection() as java.net.HttpURLConnection
                            connection.requestMethod = "GET"
                            connection.connectTimeout = 3000
                            connection.readTimeout = 3000
                            connection.setRequestProperty("Host", "epub-audiobook-service-ab00bb696e09.herokuapp.com")
                            connection.responseCode == 200
                        } catch (e: Exception) {
                            Log.e("MainActivity", "Direct IP test failed: ${e.message}")
                            false
                        }
                    }
                }
                
                val results = "Network Test Results:\n" +
                        "System reports network: ${isNetworkAvailable()}\n" +
                        "Google DNS reachable: ${googleDnsTest ?: "timeout"}\n" +
                        "Hostname resolves: ${hostnameTest ?: "timeout"}\n" +
                        "Direct IP works: ${ipTest ?: "timeout"}"
                
                Log.d("MainActivity", results)
                Toast.makeText(this@MainActivity, results, Toast.LENGTH_LONG).show()
                
            } catch (e: Exception) {
                Log.e("MainActivity", "Network test error: ${e.message}", e)
                Toast.makeText(this@MainActivity, "Network test failed: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    private fun loadDemoAudiobooks() {
        audiobooks.clear()
        
        // Create demo chapters for book 1
        val demoChapters1 = listOf(
            Chapter(
                chapter = 1,
                title = "Chapter 1: Introduction",
                url = "https://demo.audio/ch1.mp3",
                r2_key = "demo/ch1",
                duration = 1800
            ),
            Chapter(
                chapter = 2,
                title = "Chapter 2: Fundamental Techniques",
                url = "https://demo.audio/ch2.mp3",
                r2_key = "demo/ch2",
                duration = 2100
            ),
            Chapter(
                chapter = 3,
                title = "Chapter 3: Ways to Win People",
                url = "https://demo.audio/ch3.mp3",
                r2_key = "demo/ch3",
                duration = 1950
            ),
            Chapter(
                chapter = 4,
                title = "Chapter 4: How to Change People",
                url = "https://demo.audio/ch4.mp3",
                r2_key = "demo/ch4",
                duration = 2200
            )
        )
        
        // Create demo chapters for book 2
        val demoChapters2 = listOf(
            Chapter(
                chapter = 1,
                title = "Chapter 1: Start",
                url = "https://demo.audio/lean-ch1.mp3",
                r2_key = "demo/lean-ch1",
                duration = 1500
            ),
            Chapter(
                chapter = 2,
                title = "Chapter 2: Define",
                url = "https://demo.audio/lean-ch2.mp3",
                r2_key = "demo/lean-ch2",
                duration = 1600
            ),
            Chapter(
                chapter = 3,
                title = "Chapter 3: Learn",
                url = "https://demo.audio/lean-ch3.mp3",
                r2_key = "demo/lean-ch3",
                duration = 1700
            ),
            Chapter(
                chapter = 4,
                title = "Chapter 4: Experiment",
                url = "https://demo.audio/lean-ch4.mp3",
                r2_key = "demo/lean-ch4",
                duration = 1800
            )
        )
        
        // Create demo audiobooks with correct constructor parameters
        val demoBook1 = Audiobook(
            id = "demo-how-to-win-friends",
            title = "How To Win Friends and Influence People",
            author = "Dale Carnegie",
            chapters = 4,
            created_at = "2025-08-13T09:00:00.000000",
            download_url = "/api/demo/how-to-win-friends",
            isDownloaded = false,
            localPath = null,
            chaptersList = demoChapters1
        )
        
        val demoBook2 = Audiobook(
            id = "demo-lean-startup",
            title = "The Lean Startup",
            author = "Eric Ries",
            chapters = 24,
            created_at = "2025-08-13T09:00:00.000000",
            download_url = "/api/demo/lean-startup",
            isDownloaded = false,
            localPath = null,
            chaptersList = demoChapters2
        )
        
        audiobooks.add(demoBook1)
        audiobooks.add(demoBook2)
        
        // Check if any demo books exist locally
        audiobooks.forEach { audiobook ->
            audiobook.isDownloaded = fileManager.isAudiobookDownloaded(audiobook.id)
            if (audiobook.isDownloaded) {
                audiobook.localPath = fileManager.getAudiobookPath(audiobook.id)
            }
        }
        
        audiobookAdapter.updateAudiobooks(audiobooks)
        updateEmptyState()
        
        Log.d("MainActivity", "Loaded ${audiobooks.size} demo audiobooks for presentation")
    }
    
    private fun syncAudiobooks(userId: String) {
        lifecycleScope.launch {
            try {
                // Check network connectivity first
                if (!isNetworkAvailable()) {
                    tvSyncStatus.text = "No internet connection available"
                    Toast.makeText(this@MainActivity, "Please check your internet connection", Toast.LENGTH_LONG).show()
                    return@launch
                }
                
                // Start monitoring processing status
                startProcessingStatusMonitoring()
                
                // Sync audiobooks
                showLoading(true)
                tvSyncStatus.text = "Syncing audiobooks..."
                
                Log.d("MainActivity", "Requesting audiobooks for userId: $userId")
                Log.d("MainActivity", "Network available: ${isNetworkAvailable()}")
                Log.d("MainActivity", "API URL: ${ApiConfig.BASE_URL}api/audiobooks/$userId")
                
                val response = withTimeoutOrNull(60000) {
                    Log.d("MainActivity", "Starting API call...")
                    try {
                        val result = ApiConfig.apiService.getUserAudiobooks(userId)
                        Log.d("MainActivity", "API call completed successfully")
                        result
                    } catch (e: Exception) {
                        Log.e("MainActivity", "API call failed: ${e.message}", e)
                        throw RuntimeException("API call failed: ${e.message}")
                    }
                }
                
                if (response?.isSuccessful == true && response.body() != null) {
                    val audiobookResponse = response.body()!!
                    Log.d("MainActivity", "API Response: ${audiobookResponse.total} audiobooks found")
                    audiobooks.clear()
                    
                    // Show all audiobooks (user wants to see all 17 instead of unique titles only)
                    val allAudiobooks = audiobookResponse.audiobooks.sortedBy { it.title }
                    
                    audiobooks.addAll(allAudiobooks)
                    Log.d("MainActivity", "Loaded all audiobooks: ${audiobooks.size} total audiobooks")
                    
                    // Remove duplicates by keeping only the most recent copy of each title
                    val dedupedAudiobooks = audiobooks
                        .groupBy { it.title.trim().lowercase() }
                        .mapValues { (_, books) -> 
                            books.maxByOrNull { it.id } // Keep the most recent by ID (assuming newer IDs come later)
                        }
                        .values
                        .filterNotNull()
                        .toMutableList()
                    
                    if (dedupedAudiobooks.size < audiobooks.size) {
                        Log.d("MainActivity", "Deduplicated: ${audiobooks.size} -> ${dedupedAudiobooks.size} audiobooks")
                    }
                    audiobooks.clear()
                    audiobooks.addAll(dedupedAudiobooks)
                    
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
                    val errorMsg = response?.message() ?: "Connection timeout"
                    val statusCode = response?.code() ?: -1
                    Log.e("MainActivity", "API Error: $statusCode - $errorMsg")
                    
                    // For presentation - load demo audiobooks if sync fails
                    loadDemoAudiobooks()
                    
                    tvSyncStatus.text = "Using offline demo audiobooks for presentation"
                    Toast.makeText(this@MainActivity, "Demo mode: showing sample audiobooks", Toast.LENGTH_SHORT).show()
                }
                
            } catch (e: Exception) {
                Log.e("MainActivity", "Sync exception: ${e.message}", e)
                
                // For presentation - load demo audiobooks if sync fails
                loadDemoAudiobooks()
                
                val errorMessage = when {
                    e.message?.contains("Unable to resolve host") == true -> 
                        "Demo mode: Network unavailable, showing sample audiobooks"
                    e.message?.contains("timeout") == true -> 
                        "Demo mode: Server timeout, showing sample audiobooks"
                    else -> "Demo mode: Sync failed, showing sample audiobooks"
                }
                tvSyncStatus.text = errorMessage
                Toast.makeText(this@MainActivity, errorMessage, Toast.LENGTH_LONG).show()
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

    private fun deleteAudiobookFromServer(audiobook: Audiobook) {
        lifecycleScope.launch {
            try {
                val userId = currentUserId ?: return@launch
                
                // Show confirmation dialog
                val confirmed = showDeleteConfirmationDialog(audiobook.title)
                if (!confirmed) return@launch
                
                Toast.makeText(this@MainActivity, "Deleting ${audiobook.title} from server...", Toast.LENGTH_SHORT).show()
                Log.d("MainActivity", "Attempting to delete audiobook: ${audiobook.id} for user: $userId")
                
                val response = ApiConfig.apiService.deleteAudiobook(userId, audiobook.id)
                Log.d("MainActivity", "Delete response: ${response.code()} - ${response.message()}")
                
                if (response.isSuccessful) {
                    withContext(Dispatchers.Main) {
                        // Remove from local list and update UI immediately
                        val index = audiobooks.indexOf(audiobook)
                        if (index != -1) {
                            audiobooks.removeAt(index)
                            audiobookAdapter.notifyItemRemoved(index)
                            updateEmptyState()
                            Log.d("MainActivity", "Removed audiobook at index $index from UI")
                        }
                        
                        // Also delete local files if they exist
                        if (audiobook.isDownloaded) {
                            fileManager.deleteAudiobook(audiobook.id)
                        }
                        
                        Toast.makeText(this@MainActivity, "Deleted ${audiobook.title} from server", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    withContext(Dispatchers.Main) {
                        Toast.makeText(this@MainActivity, "Failed to delete from server: ${response.message()}", Toast.LENGTH_SHORT).show()
                    }
                }
                
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Delete error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun deleteAllCopiesOfBook(audiobook: Audiobook) {
        lifecycleScope.launch {
            try {
                val userId = currentUserId ?: return@launch
                
                // Find all copies with the same title
                val duplicates = audiobooks.filter { it.title.trim().lowercase() == audiobook.title.trim().lowercase() }
                
                if (duplicates.size <= 1) {
                    Toast.makeText(this@MainActivity, "Only one copy exists. Use 'Delete from Cloud' if you want to permanently remove it.", Toast.LENGTH_LONG).show()
                    return@launch
                }
                
                // Show confirmation dialog
                val confirmed = showDeleteDuplicatesConfirmationDialog(audiobook.title, duplicates.size)
                if (!confirmed) return@launch
                
                Toast.makeText(this@MainActivity, "Deleting all ${duplicates.size} copies of ${audiobook.title}...", Toast.LENGTH_SHORT).show()
                
                val deletedIndices = mutableListOf<Int>()
                var deletedCount = 0
                
                for (duplicate in duplicates) {
                    Log.d("MainActivity", "Deleting duplicate: ${duplicate.id}")
                    val response = ApiConfig.apiService.deleteAudiobook(userId, duplicate.id)
                    
                    if (response.isSuccessful) {
                        val index = audiobooks.indexOf(duplicate)
                        if (index != -1) {
                            deletedIndices.add(index)
                            
                            // Also delete local files if they exist
                            if (duplicate.isDownloaded) {
                                fileManager.deleteAudiobook(duplicate.id)
                            }
                            deletedCount++
                        }
                    }
                }
                
                withContext(Dispatchers.Main) {
                    // Remove items in reverse order to maintain indices
                    deletedIndices.sortedDescending().forEach { index ->
                        audiobooks.removeAt(index)
                        audiobookAdapter.notifyItemRemoved(index)
                    }
                    updateEmptyState()
                    
                    Toast.makeText(this@MainActivity, "Deleted $deletedCount copies of ${audiobook.title}", Toast.LENGTH_SHORT).show()
                }
                
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Delete duplicates error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private suspend fun showDeleteDuplicatesConfirmationDialog(bookTitle: String, count: Int): Boolean {
        return withContext(Dispatchers.Main) {
            suspendCancellableCoroutine<Boolean> { continuation ->
                val dialog = androidx.appcompat.app.AlertDialog.Builder(this@MainActivity)
                    .setTitle("Delete All Copies")
                    .setMessage("This will delete ALL $count copies of \"$bookTitle\" from the cloud server.\n\n" +
                               "⚠️ This will permanently remove:\n" +
                               "• All $count versions from the cloud\n" +
                               "• All local downloads of this book\n\n" +
                               "This is useful for cleaning up duplicates when you have multiple copies of the same book.")
                    .setPositiveButton("Delete All $count Copies") { _, _ -> 
                        if (continuation.isActive) {
                            continuation.resume(true, null)
                        }
                    }
                    .setNegativeButton("Cancel") { _, _ -> 
                        if (continuation.isActive) {
                            continuation.resume(false, null)
                        }
                    }
                    .setCancelable(true)
                    .setOnCancelListener {
                        if (continuation.isActive) {
                            continuation.resume(false, null)
                        }
                    }
                    .create()
                
                continuation.invokeOnCancellation { dialog.dismiss() }
                dialog.show()
            }
        }
    }
    
    private suspend fun showDeleteConfirmationDialog(bookTitle: String): Boolean {
        return withContext(Dispatchers.Main) {
            suspendCancellableCoroutine<Boolean> { continuation ->
                val dialog = androidx.appcompat.app.AlertDialog.Builder(this@MainActivity)
                    .setTitle("⚠️ Permanent Cloud Deletion")
                    .setMessage("This will PERMANENTLY DELETE \"$bookTitle\" from the cloud server.\n\n" +
                               "⚠️ WARNING: This action cannot be undone!\n" +
                               "• The audiobook will be removed from ALL your devices\n" +
                               "• You'll need to re-upload the EPUB to recreate it\n\n" +
                               "💡 TIP: Use 'Delete Local Copy' if you only want to free up device storage.")
                    .setPositiveButton("PERMANENTLY DELETE") { _, _ -> 
                        if (continuation.isActive) {
                            continuation.resume(true, null)
                        }
                    }
                    .setNegativeButton("Cancel") { _, _ -> 
                        if (continuation.isActive) {
                            continuation.resume(false, null)
                        }
                    }
                    .setCancelable(true)
                    .setOnCancelListener {
                        if (continuation.isActive) {
                            continuation.resume(false, null)
                        }
                    }
                    .create()
                
                continuation.invokeOnCancellation { dialog.dismiss() }
                dialog.show()
            }
        }
    }

    private fun openPlayer(audiobook: Audiobook) {
        // Check if this is a demo audiobook
        if (audiobook.id.startsWith("demo-")) {
            // Demo audiobooks already have chapter details
            Toast.makeText(this@MainActivity, "Opening demo audiobook: ${audiobook.title}", Toast.LENGTH_SHORT).show()
            val intent = Intent(this@MainActivity, PlayerActivity::class.java)
            intent.putExtra("audiobook", audiobook)
            startActivity(intent)
            return
        }
        
        // Load chapter details for streaming before opening player (real audiobooks)
        lifecycleScope.launch {
            try {
                val response = ApiConfig.apiService.getAudiobookDetails(audiobook.id)
                if (response.isSuccessful && response.body() != null) {
                    val details = response.body()!!
                    audiobook.chaptersList = details.chapters
                    
                    val intent = Intent(this@MainActivity, PlayerActivity::class.java)
                    intent.putExtra("audiobook", audiobook)
                    startActivity(intent)
                } else {
                    Toast.makeText(this@MainActivity, "Failed to load audiobook details", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun showLoading(show: Boolean) {
        progressLoading.visibility = if (show) View.VISIBLE else View.GONE
        btnSync.isEnabled = !show
    }

    private fun updateEmptyState() {
        emptyState.visibility = if (audiobooks.isEmpty()) View.VISIBLE else View.GONE
        rvAudiobooks.visibility = if (audiobooks.isEmpty()) View.GONE else View.VISIBLE
    }
    
    private fun startProcessingStatusMonitoring() {
        lifecycleScope.launch {
            try {
                // Check processing status every 5 seconds
                while (true) {
                    val response = ApiConfig.apiService.getProcessingStatus()
                    
                    if (response.isSuccessful && response.body() != null) {
                        val status = response.body()!!
                        updateProcessingStatus(status)
                        
                        // If no active jobs, hide the processing card after a delay
                        if (status.total_active == 0) {
                            delay(2000) // Show for 2 more seconds
                            hideProcessingStatus()
                            break
                        }
                    }
                    
                    delay(5000) // Check every 5 seconds
                }
            } catch (e: Exception) {
                Log.e("MainActivity", "Processing status monitoring error: ${e.message}")
                hideProcessingStatus()
            }
        }
    }
    
    private fun updateProcessingStatus(status: ProcessingStatus) {
        if (status.total_active > 0) {
            processingStatusCard.visibility = View.VISIBLE
            
            val activeJob = status.active_jobs.firstOrNull()
            if (activeJob != null) {
                tvProcessingTitle.text = "Converting: ${activeJob.book_title}"
                progressProcessing.progress = activeJob.progress
                
                val details = when {
                    activeJob.total_chapters != null && activeJob.current_chapter != null -> 
                        "${activeJob.message} (Chapter ${activeJob.current_chapter}/${activeJob.total_chapters})"
                    else -> activeJob.message
                }
                tvProcessingDetails.text = details
            } else {
                tvProcessingTitle.text = "Processing EPUBs to Audiobooks..."
                tvProcessingDetails.text = "${status.total_active} job(s) active"
                progressProcessing.progress = 0
            }
        } else {
            // Show completion message briefly
            if (status.total_completed > 0) {
                tvProcessingTitle.text = "Processing Complete!"
                tvProcessingDetails.text = "${status.total_completed} audiobook(s) ready"
                progressProcessing.progress = 100
            }
        }
    }
    
    private fun hideProcessingStatus() {
        processingStatusCard.visibility = View.GONE
    }
    
    private fun showProcessingProgress(message: String, progress: Int) {
        processingStatusCard.visibility = View.VISIBLE
        tvProcessingTitle.text = "🎧 Converting EPUBs to Audiobooks"
        tvProcessingDetails.text = message
        progressProcessing.progress = progress
    }
    
    private fun startSimulatedProcessingProgress(epubCount: Int) {
        lifecycleScope.launch {
            try {
                val stages = listOf(
                    "📚 Extracting chapters from EPUBs..." to 20,
                    "🔊 Converting text to speech with EdgeTTS..." to 40,
                    "🎵 Processing audio chapters..." to 60,
                    "☁️ Uploading audiobooks to R2 storage..." to 80,
                    "✅ Finalizing audiobook metadata..." to 95
                )
                
                for ((message, progress) in stages) {
                    showProcessingProgress(message, progress)
                    delay(15000) // 15 seconds per stage = ~75 seconds total
                }
                
                // Final completion check
                showProcessingProgress("🔍 Checking completion status...", 100)
                delay(5000)
                
                // Auto-sync to check for new audiobooks
                currentUserId?.let { userId ->
                    tvProcessingTitle.text = "✅ Processing Complete!"
                    tvProcessingDetails.text = "Checking for new audiobooks..."
                    delay(2000)
                    syncAudiobooks(userId)
                }
                
                hideProcessingStatus()
                
            } catch (e: Exception) {
                Log.e("MainActivity", "Simulated progress error: ${e.message}")
                hideProcessingStatus()
            }
        }
    }
    
    private fun processAllEpubs() {
        lifecycleScope.launch {
            try {
                showLoading(true)
                tvSyncStatus.text = "Processing EPUBs from R2 storage..."
                
                // Show processing status immediately
                showProcessingProgress("Checking for EPUBs in storage...", 10)
                
                val response = ApiConfig.apiService.processAllEpubs()
                
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    val message = result["message"] as? String ?: "Processing started"
                    val epubFiles = result["epub_files"] as? List<*> ?: emptyList<Any>()
                    
                    tvSyncStatus.text = "$message (${epubFiles.size} files found)"
                    Toast.makeText(this@MainActivity, "EPUB processing started!", Toast.LENGTH_SHORT).show()
                    
                    // Start simulated progress for processing
                    if (epubFiles.isNotEmpty()) {
                        startSimulatedProcessingProgress(epubFiles.size)
                    } else {
                        hideProcessingStatus()
                    }
                    
                } else {
                    tvSyncStatus.text = "Failed to process EPUBs: ${response.message()}"
                    Toast.makeText(this@MainActivity, "Failed to process EPUBs", Toast.LENGTH_SHORT).show()
                    hideProcessingStatus()
                }
                
            } catch (e: Exception) {
                tvSyncStatus.text = "Error processing EPUBs: ${e.message}"
                Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
                hideProcessingStatus()
            } finally {
                showLoading(false)
            }
        }
    }
    
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        
        if (requestCode == QR_SCANNER_REQUEST_CODE && resultCode == RESULT_OK) {
            val authenticatedUserId = data?.getStringExtra("authenticated_user_id")
            if (authenticatedUserId != null) {
                // QR authentication successful
                etUserId.setText(authenticatedUserId)
                currentUserId = authenticatedUserId
                saveUserId(authenticatedUserId)
                
                // Automatically sync audiobooks
                Toast.makeText(this, "QR login successful! Syncing audiobooks...", Toast.LENGTH_SHORT).show()
                syncAudiobooks(authenticatedUserId)
            }
        }
    }
}