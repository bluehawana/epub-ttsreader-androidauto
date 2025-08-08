package com.audiobookplayer.services

import com.audiobookplayer.models.AudiobookDetails
import com.audiobookplayer.models.AudiobookResponse
import com.audiobookplayer.models.AuthTokenVerification
import com.audiobookplayer.models.JobStatus
import com.audiobookplayer.models.ProcessingStatus
import com.audiobookplayer.models.QRCodeData
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface AudiobookApiService {
    
    @GET("/api/audiobooks/{userId}")
    suspend fun getUserAudiobooks(@Path("userId") userId: String): Response<AudiobookResponse>
    
    @GET("/api/download/{audiobookId}")
    suspend fun getAudiobookDetails(@Path("audiobookId") audiobookId: String): Response<AudiobookDetails>
    
    @GET("/health")
    suspend fun getHealthStatus(): Response<Map<String, Any>>
    
    @GET("/api/job-status/{jobId}")
    suspend fun getJobStatus(@Path("jobId") jobId: String): Response<JobStatus>
    
    @GET("/api/processing-status")
    suspend fun getProcessingStatus(): Response<ProcessingStatus>
    
    @GET("/api/verify-auth-token/{token}")
    suspend fun verifyAuthToken(@Path("token") token: String): Response<AuthTokenVerification>
    
    @POST("/api/process-all-epubs")
    suspend fun processAllEpubs(): Response<Map<String, Any>>
    
    @GET("/api/generate-auth-qr/{userId}")
    suspend fun generateAuthQR(@Path("userId") userId: String): Response<QRCodeData>
}

object ApiConfig {
    const val BASE_URL = "https://epub-audiobook-service-ab00bb696e09.herokuapp.com/"
    
    // Retrofit instance with timeout configuration
    val retrofit: retrofit2.Retrofit by lazy {
        val okHttpClient = okhttp3.OkHttpClient.Builder()
            .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .writeTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .build()
            
        retrofit2.Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(retrofit2.converter.gson.GsonConverterFactory.create())
            .build()
    }
    
    val apiService: AudiobookApiService by lazy {
        retrofit.create(AudiobookApiService::class.java)
    }
}