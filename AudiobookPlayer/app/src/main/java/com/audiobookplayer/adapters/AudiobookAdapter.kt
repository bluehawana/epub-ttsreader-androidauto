package com.audiobookplayer.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.PopupMenu
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.audiobookplayer.R
import com.audiobookplayer.models.Audiobook
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.LinearProgressIndicator

class AudiobookAdapter(
    private var audiobooks: List<Audiobook>,
    private val onPlayClick: (Audiobook) -> Unit,
    private val onDownloadClick: (Audiobook) -> Unit,
    private val onDeleteClick: (Audiobook) -> Unit,
    private val onDeleteFromServerClick: (Audiobook) -> Unit,
    private val onDeleteDuplicatesClick: (Audiobook) -> Unit
) : RecyclerView.Adapter<AudiobookAdapter.AudiobookViewHolder>() {

    fun updateAudiobooks(newAudiobooks: List<Audiobook>) {
        audiobooks = newAudiobooks.toList()
        notifyDataSetChanged()
    }
    
    private fun areListsEqual(oldList: List<Audiobook>, newList: List<Audiobook>): Boolean {
        if (oldList.size != newList.size) return false
        
        for (i in oldList.indices) {
            val oldBook = oldList[i]
            val newBook = newList[i]
            
            if (oldBook.id != newBook.id || 
                oldBook.title != newBook.title ||
                oldBook.isDownloaded != newBook.isDownloaded ||
                oldBook.chapters != newBook.chapters) {
                return false
            }
        }
        return true
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AudiobookViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_audiobook, parent, false)
        return AudiobookViewHolder(view)
    }

    override fun onBindViewHolder(holder: AudiobookViewHolder, position: Int) {
        holder.bind(audiobooks[position])
    }

    override fun getItemCount(): Int = audiobooks.size

    inner class AudiobookViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvTitle: TextView = itemView.findViewById(R.id.tvTitle)
        private val tvAuthor: TextView = itemView.findViewById(R.id.tvAuthor)
        private val tvChapters: TextView = itemView.findViewById(R.id.tvChapters)
        private val tvStatus: TextView = itemView.findViewById(R.id.tvStatus)
        private val btnPlay: MaterialButton = itemView.findViewById(R.id.btnPlay)
        private val btnDownload: MaterialButton = itemView.findViewById(R.id.btnDownload)
        private val menuButton: ImageButton = itemView.findViewById(R.id.menuButton)
        private val progressDownload: LinearProgressIndicator = itemView.findViewById(R.id.progressDownload)

        fun bind(audiobook: Audiobook) {
            tvTitle.text = audiobook.title
            tvAuthor.text = audiobook.author ?: "Unknown Author"
            tvChapters.text = "${audiobook.chapters} chapters"
            
            // Update UI based on download status - Enable streaming for all books
            when {
                audiobook.isDownloaded -> {
                    tvStatus.text = "Downloaded"
                    tvStatus.setBackgroundResource(R.drawable.rounded_background_success)
                    btnPlay.isEnabled = true
                    btnDownload.text = "Re-download"
                    btnDownload.setIconResource(R.drawable.ic_refresh)
                    progressDownload.visibility = View.GONE
                }
                else -> {
                    tvStatus.text = "Stream"
                    tvStatus.setBackgroundResource(R.drawable.rounded_background_primary)
                    btnPlay.isEnabled = true  // Enable streaming playback
                    btnDownload.text = "Download"
                    btnDownload.setIconResource(R.drawable.ic_download)
                    progressDownload.visibility = View.GONE
                }
            }

            // Click listeners - Allow both downloaded and streaming playback
            btnPlay.setOnClickListener { 
                onPlayClick(audiobook)  // Always allow playback - will stream if not downloaded
            }
            
            btnDownload.setOnClickListener { 
                onDownloadClick(audiobook)
                // Show progress during download
                progressDownload.visibility = View.VISIBLE
                progressDownload.isIndeterminate = true
            }

            // Menu popup
            menuButton.setOnClickListener { view ->
                showPopupMenu(view, audiobook)
            }
            
            // Item click to play - allow streaming
            itemView.setOnClickListener {
                onPlayClick(audiobook)  // Always allow playback
            }
        }

        private fun showPopupMenu(view: View, audiobook: Audiobook) {
            val popup = PopupMenu(view.context, view)
            popup.menuInflater.inflate(R.menu.audiobook_menu, popup.menu)
            
            // Show/hide menu items based on status
            popup.menu.findItem(R.id.menu_play).isVisible = audiobook.isDownloaded
            popup.menu.findItem(R.id.menu_delete_local).isVisible = audiobook.isDownloaded
            
            popup.setOnMenuItemClickListener { item ->
                when (item.itemId) {
                    R.id.menu_play -> {
                        onPlayClick(audiobook)
                        true
                    }
                    R.id.menu_download -> {
                        onDownloadClick(audiobook)
                        true
                    }
                    R.id.menu_delete_local -> {
                        onDeleteClick(audiobook)
                        true
                    }
                    R.id.menu_delete_server -> {
                        onDeleteFromServerClick(audiobook)
                        true
                    }
                    R.id.menu_delete_duplicates -> {
                        onDeleteDuplicatesClick(audiobook)
                        true
                    }
                    R.id.menu_details -> {
                        // TODO: Show audiobook details
                        true
                    }
                    else -> false
                }
            }
            popup.show()
        }
    }
}