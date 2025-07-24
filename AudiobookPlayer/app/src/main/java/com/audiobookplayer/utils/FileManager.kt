package com.audiobookplayer.utils

import android.content.Context
import com.audiobookplayer.models.Chapter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class FileManager(private val context: Context) {
    
    private val httpClient = OkHttpClient()
    private val audiobooksDir: File
        get() = File(context.getExternalFilesDir(null), "audiobooks").apply { 
            if (!exists()) mkdirs() 
        }

    fun isAudiobookDownloaded(audiobookId: String): Boolean {
        val audiobookDir = File(audiobooksDir, audiobookId)
        return audiobookDir.exists() && audiobookDir.listFiles()?.isNotEmpty() == true
    }

    fun getAudiobookPath(audiobookId: String): String {
        return File(audiobooksDir, audiobookId).absolutePath
    }

    suspend fun downloadAudiobook(
        audiobookId: String, 
        title: String, 
        chapters: List<Chapter>
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            val audiobookDir = File(audiobooksDir, audiobookId)
            if (!audiobookDir.exists()) {
                audiobookDir.mkdirs()
            }

            // Create metadata file
            val metadataFile = File(audiobookDir, "metadata.json")
            val metadata = """
                {
                    "id": "$audiobookId",
                    "title": "$title",
                    "chapters": ${chapters.size},
                    "downloadDate": "${System.currentTimeMillis()}"
                }
            """.trimIndent()
            metadataFile.writeText(metadata)

            // Download each chapter
            chapters.forEachIndexed { index, chapter ->
                val chapterFile = File(audiobookDir, "chapter_${chapter.chapter}.mp3")
                
                if (!chapterFile.exists()) {
                    val success = downloadFile(chapter.url, chapterFile)
                    if (!success) {
                        // If download fails, clean up and return false
                        audiobookDir.deleteRecursively()
                        return@withContext false
                    }
                }
            }
            
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    private suspend fun downloadFile(url: String, file: File): Boolean = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder().url(url).build()
            val response = httpClient.newCall(request).execute()
            
            if (response.isSuccessful) {
                response.body?.let { body ->
                    FileOutputStream(file).use { output ->
                        body.byteStream().copyTo(output)
                    }
                    true
                } ?: false
            } else {
                false
            }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    fun deleteAudiobook(audiobookId: String): Boolean {
        return try {
            val audiobookDir = File(audiobooksDir, audiobookId)
            audiobookDir.deleteRecursively()
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    fun getChapterFiles(audiobookId: String): List<File> {
        val audiobookDir = File(audiobooksDir, audiobookId)
        return audiobookDir.listFiles { _, name -> 
            name.startsWith("chapter_") && name.endsWith(".mp3") 
        }?.sortedBy { 
            // Sort by chapter number
            it.name.removePrefix("chapter_").removeSuffix(".mp3").toIntOrNull() ?: 0
        } ?: emptyList()
    }

    fun getTotalSize(): Long {
        return audiobooksDir.walkTopDown()
            .filter { it.isFile }
            .map { it.length() }
            .sum()
    }

    fun getTotalSizeFormatted(): String {
        val bytes = getTotalSize()
        return when {
            bytes < 1024 -> "$bytes B"
            bytes < 1024 * 1024 -> "${bytes / 1024} KB"
            bytes < 1024 * 1024 * 1024 -> "${bytes / (1024 * 1024)} MB"
            else -> "${bytes / (1024 * 1024 * 1024)} GB"
        }
    }
}