package com.audiobookplayer.models

import java.io.Serializable

data class Audiobook(
    val id: String,
    val title: String,
    val author: String? = "Unknown Author",
    val chapters: List<Chapter>,
    val totalChapters: Int,
    val createdAt: String,
    val downloadUrl: String,
    var isDownloaded: Boolean = false,
    var localPath: String? = null,
    var currentChapter: Int = 0,
    var currentPosition: Long = 0L,
    var totalDuration: Long = 0L
) : Serializable

data class Chapter(
    val chapter: Int,
    val title: String,
    val url: String,
    val r2Key: String,
    val duration: Int,
    var localPath: String? = null,
    var isDownloaded: Boolean = false
) : Serializable

data class AudiobookResponse(
    val audiobooks: List<Audiobook>,
    val total: Int
)

data class AudiobookDetails(
    val audiobookId: String,
    val title: String,
    val chapters: List<Chapter>,
    val totalChapters: Int
)