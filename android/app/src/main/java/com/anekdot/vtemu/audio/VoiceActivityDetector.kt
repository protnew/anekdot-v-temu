package com.anekdot.vtemu.audio

import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.io.File
import java.io.RandomAccessFile

/**
 * Voice Activity Detector — energy-based VAD.
 * Listens to microphone in background, triggers callback when speech is detected.
 * 2KB equivalent in logic (no model needed for energy-based VAD).
 */
class VoiceActivityDetector(
    private val context: Context,
    private val speechThreshold: Double = 0.02,
    private val silenceThreshold: Double = 0.005,
    private val speechFrames: Int = 5,
    private val silenceFrames: Int = 15
) {
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private val _isListening = MutableStateFlow(false)
    val isListening: StateFlow<Boolean> = _isListening

    private val _isSpeechDetected = MutableStateFlow(false)
    val isSpeechDetected: StateFlow<Boolean> = _isSpeechDetected

    var onSpeechStart: (() -> Unit)? = null
    var onSpeechEnd: ((ByteArray) -> Unit)? = null

    private var audioRecord: AudioRecord? = null
    private var isRunning = false
    private var speechBuffer = mutableListOf<ShortArray>()
    private var speechFrameCount = 0
    private var silenceFrameCount = 0

    companion object {
        private const val TAG = "VAD"
        private const val SAMPLE_RATE = 16000
        private const val BUFFER_SIZE_FRAMES = 512  // 32ms chunks
    }

    fun startListening() {
        if (isRunning) return
        isRunning = true
        _isListening.value = true
        scope.launch {
            listenLoop()
        }
    }

    fun stopListening() {
        isRunning = false
        _isListening.value = false
        audioRecord?.let {
            try { it.stop(); it.release() } catch (_: Exception) {}
        }
        audioRecord = null
    }

    private fun listenLoop() {
        val minBuf = AudioRecord.getMinBufferSize(
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )
        val bufSize = maxOf(minBuf, BUFFER_SIZE_FRAMES * 2)

        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            bufSize
        )

        audioRecord?.startRecording()

        val buffer = ShortArray(BUFFER_SIZE_FRAMES)

        while (isRunning) {
            val read = audioRecord?.read(buffer, 0, BUFFER_SIZE_FRAMES) ?: 0
            if (read <= 0) continue

            val rms = calculateRms(buffer, read)
            val isSpeech = rms > speechThreshold

            if (isSpeech) {
                speechFrameCount++
                silenceFrameCount = 0
                speechBuffer.add(buffer.copyOf(read))

                if (speechFrameCount == this.speechFrames && !_isSpeechDetected.value) {
                    _isSpeechDetected.value = true
                    onSpeechStart?.invoke()
                }
            } else {
                silenceFrameCount++

                if (_isSpeechDetected.value) {
                    // Still accumulate during silence gaps within speech
                    if (silenceFrameCount < 3) {
                        speechBuffer.add(buffer.copyOf(read))
                    }
                }

                if (silenceFrameCount >= silenceFrames && _isSpeechDetected.value) {
                    _isSpeechDetected.value = false
                    // Speech ended — collect audio and send
                    val audioData = collectAudio()
                    onSpeechEnd?.invoke(audioData)
                    speechBuffer.clear()
                    speechFrameCount = 0
                    silenceFrameCount = 0
                }
            }
        }

        audioRecord?.let {
            try { it.stop(); it.release() } catch (_: Exception) {}
        }
    }

    private fun calculateRms(buffer: ShortArray, len: Int): Double {
        var sum = 0.0
        for (i in 0 until len) {
            val sample = buffer[i].toDouble() / 32768.0
            sum += sample * sample
        }
        return Math.sqrt(sum / len)
    }

    private fun collectAudio(): ByteArray {
        // Combine all buffered frames into a single WAV byte array
        var totalSamples = 0
        for (chunk in speechBuffer) {
            totalSamples += chunk.size
        }

        // Create WAV with header
        val dataSize = totalSamples * 2  // 16-bit = 2 bytes per sample
        val wavSize = 44 + dataSize
        val wav = ByteArray(wavSize)

        // WAV header
        writeString(wav, 0, "RIFF")
        writeInt(wav, 4, wavSize - 8)
        writeString(wav, 8, "WAVE")
        writeString(wav, 12, "fmt ")
        writeInt(wav, 16, 16)  // PCM
        writeShort(wav, 20, 1.toShort())  // PCM format
        writeShort(wav, 22, 1.toShort())  // mono
        writeInt(wav, 24, SAMPLE_RATE)
        writeInt(wav, 28, SAMPLE_RATE * 2)  // byte rate
        writeShort(wav, 32, 2.toShort())  // block align
        writeShort(wav, 34, 16.toShort())  // bits per sample
        writeString(wav, 36, "data")
        writeInt(wav, 40, dataSize)

        var offset = 44
        for (chunk in speechBuffer) {
            for (sample in chunk) {
                wav[offset++] = (sample.toInt() and 0xFF).toByte()
                wav[offset++] = (sample.toInt() shr 8 and 0xFF).toByte()
            }
        }

        return wav
    }

    private fun writeString(arr: ByteArray, offset: Int, s: String) {
        for (i in s.indices) arr[offset + i] = s[i].code.toByte()
    }

    private fun writeInt(arr: ByteArray, offset: Int, value: Int) {
        arr[offset] = (value and 0xFF).toByte()
        arr[offset + 1] = (value shr 8 and 0xFF).toByte()
        arr[offset + 2] = (value shr 16 and 0xFF).toByte()
        arr[offset + 3] = (value shr 24 and 0xFF).toByte()
    }

    private fun writeShort(arr: ByteArray, offset: Int, value: Short) {
        arr[offset] = (value.toInt() and 0xFF).toByte()
        arr[offset + 1] = (value.toInt() shr 8 and 0xFF).toByte()
    }

    fun release() {
        stopListening()
        scope.cancel()
    }
}
