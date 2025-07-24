package com.audiobookplayer.activities

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.audiobookplayer.R
import com.audiobookplayer.services.ApiConfig
import com.journeyapps.barcodescanner.BarcodeCallback
import com.journeyapps.barcodescanner.BarcodeResult
import com.journeyapps.barcodescanner.DecoratedBarcodeView
import kotlinx.coroutines.launch
import java.net.URL

class QRScannerActivity : AppCompatActivity() {
    
    private lateinit var barcodeView: DecoratedBarcodeView
    private val CAMERA_PERMISSION_REQUEST = 200
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_qr_scanner)
        
        barcodeView = findViewById(R.id.barcode_scanner)
        
        // Check camera permission
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) 
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this, 
                arrayOf(Manifest.permission.CAMERA), 
                CAMERA_PERMISSION_REQUEST
            )
        } else {
            startScanning()
        }
        
        // Set up toolbar
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Scan QR Code"
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == CAMERA_PERMISSION_REQUEST) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startScanning()
            } else {
                Toast.makeText(this, "Camera permission is required to scan QR codes", Toast.LENGTH_LONG).show()
                finish()
            }
        }
    }
    
    private fun startScanning() {
        barcodeView.decodeContinuous(object : BarcodeCallback {
            override fun barcodeResult(result: BarcodeResult?) {
                result?.let { 
                    handleQRCodeResult(it.text)
                }
            }
        })
    }
    
    private fun handleQRCodeResult(qrContent: String) {
        try {
            // Parse the QR code URL: https://your-backend.com/auth?token=abc123&user_id=telegram_id
            val url = URL(qrContent)
            val query = url.query
            
            if (query != null) {
                val params = query.split("&").associate { param ->
                    val (key, value) = param.split("=")
                    key to value
                }
                
                val token = params["token"]
                val userId = params["user_id"]
                
                if (token != null && userId != null) {
                    // Verify the token with the backend
                    verifyAuthToken(token, userId)
                } else {
                    showError("Invalid QR code format")
                }
            } else {
                showError("Invalid QR code")
            }
            
        } catch (e: Exception) {
            showError("Failed to parse QR code: ${e.message}")
        }
    }
    
    private fun verifyAuthToken(token: String, userId: String) {
        lifecycleScope.launch {
            try {
                val response = ApiConfig.apiService.verifyAuthToken(token)
                
                if (response.isSuccessful && response.body() != null) {
                    val authResult = response.body()!!
                    
                    if (authResult.valid && authResult.user_id == userId) {
                        // Authentication successful
                        Toast.makeText(this@QRScannerActivity, "Authentication successful!", Toast.LENGTH_SHORT).show()
                        
                        // Return the authenticated user ID to MainActivity
                        val resultIntent = Intent()
                        resultIntent.putExtra("authenticated_user_id", userId)
                        setResult(RESULT_OK, resultIntent)
                        finish()
                        
                    } else {
                        showError("Authentication failed: Invalid credentials")
                    }
                } else {
                    showError("Authentication failed: ${response.message()}")
                }
                
            } catch (e: Exception) {
                showError("Network error: ${e.message}")
            }
        }
    }
    
    private fun showError(message: String) {
        runOnUiThread {
            Toast.makeText(this, message, Toast.LENGTH_LONG).show()
            // Continue scanning after error
            barcodeView.resume()
        }
    }
    
    override fun onResume() {
        super.onResume()
        barcodeView.resume()
    }
    
    override fun onPause() {
        super.onPause()
        barcodeView.pause()
    }
    
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}