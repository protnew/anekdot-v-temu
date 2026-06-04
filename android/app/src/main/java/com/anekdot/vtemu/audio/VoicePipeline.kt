package com.anekdot.vtemu.audio

import android.content.Context
import android.util.Base64
import android.util.Log
import com.anekdot.vtemu.api.AnekdotApi
import com.anekdot.vtemu.model.ContextRequest
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Main voice pipeline coordinator.
 * Flow: Microphone → VAD → STT (server) → Context search → Show joke
 *
 * Supports two modes:
 * 1. Server mode: sends audio to /api/voice/stt → gets text → /api/jokes/context
 * 2. Local mode (future): whisper.cpp NDK runs on device
 */
class VoicePipeline(
    private val context: Context,
    private val api: AnekdotApi,
    private val baseUrl: String
) {
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    private val vad = VoiceActivityDetector(context)

    private val _state = MutableStateFlow<PipelineState>(PipelineState.Idle)
    val state: StateFlow<PipelineState> = _state

    private val _lastJokeText = MutableStateFlow<String?>(null)
    val lastJokeText: StateFlow<String?> = _lastJokeText

    private val _lastTranscription = MutableStateFlow<String?>(null)
    val lastTranscription: StateFlow<String?> = _lastTranscription

    var onJokeReady: ((String, String?) -> Unit)? = null  // jokeText, transcription

    fun start() {
        Log.d(TAG, "Starting voice pipeline")
        vad.onSpeechStart = {
            _state.value = PipelineState.Listening
            Log.d(TAG, "Speech detected!")
        }
        vad.onSpeechEnd = { audioData ->
            Log.d(TAG, "Speech ended, audio size: ${audioData.size} bytes")
            _state.value = PipelineState.Processing
            scope.launch {
                processAudio(audioData)
            }
        }
        vad.startListening()
        _state.value = PipelineState.WaitingForSpeech
    }

    fun stop() {
        vad.stopListening()
        _state.value = PipelineState.Idle
    }

    fun toggle(): Boolean {
        return if (vad.isListening.value) {
            stop()
            false
        } else {
            start()
            true
        }
    }

    private suspend fun processAudio(audioData: ByteArray) {
        try {
            // Step 1: Send audio to server for STT
            val audioBase64 = Base64.encodeToString(audioData, Base64.NO_WRAP)
            _state.value = PipelineState.Transcribing

            val sttResult = withContext(Dispatchers.IO) {
                // Use raw OkHttp call for STT (custom endpoint)
                val client = okhttp3.OkHttpClient.Builder()
                    .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
                    .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                    .build()

                val jsonBody = """
                    {"audio_base64": "$audioBase64", "format": "wav", "language": "ru"}
                """.trimIndent()

                val body = okhttp3.RequestBody.create(
                    okhttp3.MediaType.parse("application/json"),
                    jsonBody
                )

                val request = okhttp3.Request.Builder()
                    .url("$baseUrl/api/voice/stt")
                    .post(body)
                    .build()

                val response = client.newCall(request).execute()
                val responseBody = response.body()?.string() ?: "{}"

                // Parse JSON manually for simplicity
                val moshi = com.squareup.moshi.Moshi.Builder().build()
                val adapter = moshi.adapter(com.squareup.moshi.Types.mapOf(
                    String::class.java, Any::class.java
                ))
                adapter.fromJson(responseBody) ?: emptyMap()
            }

            val text = sttResult["text"] as? String ?: ""
            Log.d(TAG, "Transcribed: '$text'")

            if (text.isBlank() || text in listOf("[BLANK_AUDIO]", "[музыка]", "[ Music ]", "[MUSIC]")) {
                _state.value = PipelineState.WaitingForSpeech
                return
            }

            _lastTranscription.value = text
            _state.value = PipelineState.SearchingJoke

            // Step 2: Search for matching joke
            val jokeResult = withContext(Dispatchers.IO) {
                try {
                    api.contextJoke(ContextRequest(text = text, count = 3))
                } catch (e: Exception) {
                    Log.e(TAG, "Joke search failed", e)
                    null
                }
            }

            val jokes = jokeResult?.jokes ?: emptyList()
            if (jokes.isNotEmpty()) {
                val joke = jokes.first()
                val jokeText = joke.text
                _lastJokeText.value = jokeText
                _state.value = PipelineState.JokeReady(jokeText)
                onJokeReady?.invoke(jokeText, text)
                Log.d(TAG, "Joke found: ${jokeText.take(80)}...")
            } else {
                Log.d(TAG, "No jokes found for: '$text'")
                _state.value = PipelineState.NoMatch(text)
            }

            // Return to listening after showing joke
            delay(3000)
            if (vad.isListening.value) {
                _state.value = PipelineState.WaitingForSpeech
            }

        } catch (e: Exception) {
            Log.e(TAG, "Pipeline error", e)
            _state.value = PipelineState.Error(e.message ?: "Unknown error")
            delay(2000)
            if (vad.isListening.value) {
                _state.value = PipelineState.WaitingForSpeech
            }
        }
    }

    fun release() {
        vad.release()
        scope.cancel()
    }

    companion object {
        private const val TAG = "VoicePipeline"
    }
}

sealed class PipelineState {
    object Idle : PipelineState()
    object WaitingForSpeech : PipelineState()
    object Listening : PipelineState()
    object Processing : PipelineState()
    object Transcribing : PipelineState()
    object SearchingJoke : PipelineState()
    data class JokeReady(val joke: String) : PipelineState()
    data class NoMatch(val text: String) : PipelineState()
    data class Error(val message: String) : PipelineState()
}
