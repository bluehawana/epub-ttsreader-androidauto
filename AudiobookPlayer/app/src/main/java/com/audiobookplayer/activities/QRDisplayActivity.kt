package com.audiobookplayer.activities

import android.graphics.Bitmap
import android.os.Bundle
import android.view.View
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.audiobookplayer.R
import com.audiobookplayer.services.ApiConfig
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.zxing.BarcodeFormat
import com.google.zxing.WriterException
import com.google.zxing.common.BitMatrix
import com.google.zxing.qrcode.QRCodeWriter
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.UUID

class QRDisplayActivity : AppCompatActivity() {

    private lateinit var qrCodeImage: ImageView
    private lateinit var statusText: TextView
    private lateinit var progressLoading: CircularProgressIndicator
    
    private var authToken: String? = null
    private var isAuthenticated = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_qr_display)
        
        initViews()
        setupToolbar()
        generateAndDisplayQRCode()
        startAuthPolling()
    }

    private fun initViews() {
        qrCodeImage = findViewById(R.id.qrCodeImage)
        statusText = findViewById(R.id.statusText)
        progressLoading = findViewById(R.id.progressLoading)
    }
    
    private fun setupToolbar() {
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
    }

    private fun generateAndDisplayQRCode() {
        // Get user ID from intent or use prompt
        val userId = intent.getStringExtra("user_id")
        
        if (userId.isNullOrEmpty()) {
            // If no user ID provided, prompt user first
            Toast.makeText(this, "Please enter User ID in main screen first", Toast.LENGTH_LONG).show()
            finish()
            return
        }
        
        lifecycleScope.launch {
            try {
                // Call backend to generate QR code
                val response = ApiConfig.apiService.generateAuthQR(userId)
                
                if (response.isSuccessful && response.body() != null) {
                    val qrData = response.body()!!
                    authToken = qrData.token
                    
                    // The backend returns the complete QR URL
                    val qrBitmap = generateQRCode(qrData.qr_url, 512, 512)
                    qrCodeImage.setImageBitmap(qrBitmap)
                    progressLoading.visibility = View.GONE
                    statusText.text = "Scan this QR code with your phone's camera app"
                } else {
                    Toast.makeText(this@QRDisplayActivity, "Failed to generate QR code", Toast.LENGTH_SHORT).show()
                    finish()
                }
            } catch (e: Exception) {
                Toast.makeText(this@QRDisplayActivity, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                finish()
            }
        }
    }

    private fun generateQRCode(text: String, width: Int, height: Int): Bitmap {
        val writer = QRCodeWriter()
        val bitMatrix: BitMatrix = writer.encode(text, BarcodeFormat.QR_CODE, width, height)
        
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.RGB_565)
        for (x in 0 until width) {
            for (y in 0 until height) {
                bitmap.setPixel(x, y, if (bitMatrix[x, y]) android.graphics.Color.BLACK else android.graphics.Color.WHITE)
            }
        }
        return bitmap
    }

    private fun startAuthPolling() {
        lifecycleScope.launch {
            var attempts = 0
            val maxAttempts = 60 // 5 minutes max (5 seconds * 60)
            
            while (!isAuthenticated && attempts < maxAttempts) {
                try {
                    authToken?.let { token ->
                        val response = ApiConfig.apiService.verifyAuthToken(token)
                        
                        if (response.isSuccessful && response.body() != null) {
                            val authResult = response.body()!!
                            
                            if (authResult.valid && authResult.user_id != null) {
                                // Authentication successful!
                                isAuthenticated = true
                                statusText.text = "✅ Authentication successful!"
                                
                                // Return result to MainActivity
                                val resultIntent = intent
                                resultIntent.putExtra("authenticated_user_id", authResult.user_id)
                                setResult(RESULT_OK, resultIntent)
                                
                                Toast.makeText(this@QRDisplayActivity, "Login successful!", Toast.LENGTH_SHORT).show()
                                finish()
                                return@launch
                            }
                        }
                    }
                } catch (e: Exception) {
                    // Continue polling on error
                }
                
                attempts++
                delay(5000) // Check every 5 seconds
            }
            
            // Timeout
            if (!isAuthenticated) {
                statusText.text = "❌ Authentication timeout. Please try again."
                Toast.makeText(this@QRDisplayActivity, "Authentication timeout", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}