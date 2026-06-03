package com.anekdot.vtemu.audio

import android.content.Context
import android.media.MediaPlayer
import android.util.Log
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.TtsRequest
import com.anekdot.vtemu.repository.AnekdotRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class TtsPlayer(private val context: Context) {

    private var mediaPlayer: MediaPlayer? = null
    private var isPlayingFlag = false

    var onPlayingChanged: ((Boolean) -> Unit)? = null

    fun play(text: String, baseUrl: String, repository: AnekdotRepository) {
        if (isPlayingFlag) {
            stop()
            return
        }

        CoroutineScope(Dispatchers.Main).launch {
            when (val result = repository.textToSpeech(text)) {
                is ApiResponse.Success -> {
                    val audioUrl = baseUrl.trimEnd('/') + "/" + result.data.audioFile.trimStart('/')
                    startPlayback(audioUrl)
                }
                is ApiResponse.Error -> {
                    Log.e(TAG, "TTS error: ${result.message}")
                    onPlayingChanged?.invoke(false)
                }
            }
        }
    }

    private fun startPlayback(audioUrl: String) {
        releasePlayer()

        mediaPlayer = MediaPlayer().apply {
            setOnPreparedListener { mp ->
                mp.start()
                isPlayingFlag = true
                onPlayingChanged?.invoke(true)
            }
            setOnCompletionListener { mp ->
                isPlayingFlag = false
                onPlayingChanged?.invoke(false)
                mp.release()
                mediaPlayer = null
            }
            setOnErrorListener { mp, what, extra ->
                Log.e(TAG, "MediaPlayer error: what=$what extra=$extra")
                isPlayingFlag = false
                onPlayingChanged?.invoke(false)
                mp.release()
                mediaPlayer = null
                true
            }
            try {
                setDataSource(audioUrl)
                prepareAsync()
            } catch (e: Exception) {
                Log.e(TAG, "MediaPlayer setDataSource error", e)
                isPlayingFlag = false
                onPlayingChanged?.invoke(false)
                release()
            }
        }
    }

    fun stop() {
        mediaPlayer?.let {
            if (it.isPlaying) {
                it.stop()
            }
            it.release()
        }
        mediaPlayer = null
        isPlayingFlag = false
        onPlayingChanged?.invoke(false)
    }

    fun isPlaying(): Boolean = isPlayingFlag

    fun release() {
        stop()
    }

    private fun releasePlayer() {
        mediaPlayer?.let {
            try {
                if (it.isPlaying) it.stop()
                it.release()
            } catch (_: Exception) {
            }
        }
        mediaPlayer = null
        isPlayingFlag = false
    }

    companion object {
        private const val TAG = "TtsPlayer"
    }
}
