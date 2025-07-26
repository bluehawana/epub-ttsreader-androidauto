package com.audiobookplayer.models

import java.io.Serializable

data class Audiobook(
    val id: String,
    val title: String,
    val author: String? = "Unknown Author",
    val chapters: Int,  // Changed from List<Chapter> to Int to match API
    val created_at: String,  // Changed from createdAt to match API
    val download_url: String,  // Changed from downloadUrl to match API  
    var isDownloaded: Boolean = false,
    var localPath: String? = null,
    var currentChapter: Int = 0,
    var currentPosition: Long = 0L,
    var totalDuration: Long = 0L,
    var chaptersList: List<Chapter> = emptyList()  // Separate field for actual chapters
) : Serializable

data class Chapter(
    val chapter: Int,
    val title: String,
    val url: String,
    val r2_key: String,  // Changed from r2Key to match API
    val duration: Int,
    var localPath: String? = null,
    var isDownloaded: Boolean = false
) : Serializable

data class AudiobookResponse(
    val audiobooks: List<Audiobook>,
    val total: Int
)

data class AudiobookDetails(
    val audiobook_id: String,  // Changed from audiobookId to match API
    val title: String,
    val chapters: List<Chapter>,
    val total_chapters: Int  // Changed from totalChapters to match API
)

data class JobStatus(
    val job_id: String,
    val status: String, // "processing", "completed", "failed", "not_found"
    val progress: Int,
    val message: String,
    val book_title: String? = null,
    val user_id: String? = null,
    val started_at: String? = null,
    val completed_at: String? = null,
    val failed_at: String? = null,
    val total_chapters: Int? = null,
    val current_chapter: Int? = null,
    val chapters_processed: Int? = null,
    val error: String? = null
)

data class ProcessingJob(
    val job_id: String,
    val user_id: String,
    val book_title: String,
    val status: String,
    val progress: Int,
    val message: String,
    val started_at: String,
    val total_chapters: Int? = null,
    val current_chapter: Int? = null
)

data class ProcessingStatus(
    val active_jobs: List<ProcessingJob>,
    val total_active: Int,
    val total_completed: Int,
    val processed_epubs: Int,
    val timestamp: String
)

data class AuthTokenVerification(
    val valid: Boolean,
    val user_id: String? = null,
    val authenticated_at: String? = null,
    val error: String? = null
)

data class QRCodeData(
    val token: String,
    val qr_url: String,
    val expires_at: String
)