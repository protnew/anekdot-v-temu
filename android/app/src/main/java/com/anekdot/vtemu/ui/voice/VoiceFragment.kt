package com.anekdot.vtemu.ui.voice

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.anekdot.vtemu.AnekdotApp
import com.anekdot.vtemu.R
import com.anekdot.vtemu.audio.PipelineState
import com.anekdot.vtemu.audio.VoicePipeline
import com.google.android.material.floatingactionbutton.FloatingActionButton
import kotlinx.coroutines.launch

/**
 * Voice overlay fragment — main use case "2 friends in cafe".
 * Big floating mic button, real-time transcription, joke popup.
 */
class VoiceFragment : Fragment() {

    private lateinit var pipeline: VoicePipeline
    private lateinit var micButton: FloatingActionButton
    private lateinit var statusText: TextView
    private lateinit var transcriptionText: TextView
    private lateinit var jokeText: TextView
    private lateinit var jokeCard: View

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            startPipeline()
        } else {
            Toast.makeText(requireContext(), "Нужен микрофон для работы!", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        return inflater.inflate(R.layout.fragment_voice, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        micButton = view.findViewById(R.id.btn_mic)
        statusText = view.findViewById(R.id.tv_status)
        transcriptionText = view.findViewById(R.id.tv_transcription)
        jokeText = view.findViewById(R.id.tv_joke)
        jokeCard = view.findViewById(R.id.card_joke)

        val app = (requireActivity().application as AnekdotApp)
        val api = app.anekdotApi
        val baseUrl = app.baseUrl

        pipeline = VoicePipeline(requireContext(), api, baseUrl)

        // Observe pipeline state
        viewLifecycleOwner.lifecycleScope.launch {
            pipeline.state.collect { state ->
                when (state) {
                    is PipelineState.Idle -> {
                        statusText.text = "Нажмите 🎤 чтобы начать"
                        micButton.setImageResource(android.R.drawable.ic_btn_speak_now)
                        jokeCard.visibility = View.GONE
                    }
                    is PipelineState.WaitingForSpeech -> {
                        statusText.text = "🎙️ Слушаю... (скажите что-нибудь)"
                        micButton.setImageResource(android.R.drawable.ic_media_pause)
                    }
                    is PipelineState.Listening -> {
                        statusText.text = "👂 Говорите! Я слушаю..."
                    }
                    is PipelineState.Processing -> {
                        statusText.text = "🔄 Обрабатываю..."
                    }
                    is PipelineState.Transcribing -> {
                        statusText.text = "📝 Распознаю речь..."
                    }
                    is PipelineState.SearchingJoke -> {
                        statusText.text = "😄 Ищу шутку..."
                    }
                    is PipelineState.JokeReady -> {
                        statusText.text = "😂 Вот шутка!"
                        jokeText.text = state.joke
                        jokeCard.visibility = View.VISIBLE
                    }
                    is PipelineState.NoMatch -> {
                        statusText.text = "🤷 Не нашёл шутку для: \"${state.text.take(30)}...\""
                    }
                    is PipelineState.Error -> {
                        statusText.text = "❌ Ошибка: ${state.message}"
                    }
                }
            }
        }

        // Observe transcription
        viewLifecycleOwner.lifecycleScope.launch {
            pipeline.lastTranscription.collect { text ->
                text?.let {
                    transcriptionText.text = "\"$it\""
                    transcriptionText.visibility = View.VISIBLE
                }
            }
        }

        micButton.setOnClickListener {
            if (pipeline.state.value is PipelineState.Idle) {
                // Start
                if (hasAudioPermission()) {
                    startPipeline()
                } else {
                    requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                }
            } else {
                // Stop
                pipeline.stop()
            }
        }
    }

    private fun startPipeline() {
        pipeline.onJokeReady = { joke, transcription ->
            // Could also trigger TTS here
        }
        pipeline.start()
    }

    private fun hasAudioPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            requireContext(), Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }

    override fun onDestroyView() {
        super.onDestroyView()
        pipeline.release()
    }
}
