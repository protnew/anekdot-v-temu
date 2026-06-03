package com.anekdot.vtemu.ui.random

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.anekdot.vtemu.AnekdotApp
import com.anekdot.vtemu.R
import com.anekdot.vtemu.audio.TtsPlayer
import com.anekdot.vtemu.databinding.FragmentRandomBinding
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.util.CatEmojis
import com.anekdot.vtemu.viewmodel.RandomViewModel
import com.anekdot.vtemu.viewmodel.ViewModelFactory
import com.google.android.material.chip.Chip
import com.google.android.material.snackbar.Snackbar

class RandomFragment : Fragment() {

    private var _binding: FragmentRandomBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: RandomViewModel
    private lateinit var ttsPlayer: TtsPlayer
    private var selectedChipCategory: String? = null

    private val quickTopics = listOf(
        "💼 Работа" to "работа",
        "💻 IT" to "айти",
        "👨‍👩‍👧 Семья" to "семья",
        "💰 Деньги" to "деньги",
        "💑 Отношения" to "отношения",
        "🏥 Здоровье" to "здоровье",
        "🤖 AI" to "искусственный интеллект",
        "🐱 Котики" to "котики"
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentRandomBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val app = requireActivity().application
        val anekdotApp = AnekdotApp.getInstance(app)
        val api = anekdotApp.anekdotApi
        val repository = AnekdotRepository(api)
        val prefs = requireActivity().getSharedPreferences("anekdot_prefs", Context.MODE_PRIVATE)
        val factory = ViewModelFactory(repository, prefs)

        viewModel = ViewModelProvider(this, factory)[RandomViewModel::class.java]
        ttsPlayer = TtsPlayer(requireContext())

        // --- TTS button ---
        binding.btnTts.setOnClickListener {
            val joke = viewModel.joke.value
            if (joke == null) return@setOnClickListener

            if (ttsPlayer.isPlaying()) {
                ttsPlayer.stop()
                binding.btnTts.setImageResource(R.drawable.ic_volume)
            } else {
                val baseUrl = anekdotApp.retrofit.baseUrl().toString()
                ttsPlayer.onPlayingChanged = { playing ->
                    requireActivity().runOnUiThread {
                        binding.btnTts.setImageResource(
                            if (playing) R.drawable.ic_stop else R.drawable.ic_volume
                        )
                    }
                }
                ttsPlayer.play(joke.text, baseUrl, repository)
            }
        }

        // --- Refresh ---
        binding.fabRefresh.setOnClickListener {
            selectedChipCategory?.let { viewModel.loadRandom(it) } ?: viewModel.loadRandom()
        }

        // --- Like ---
        binding.btnLike.setOnClickListener { viewModel.like() }

        // --- Share ---
        binding.btnShare.setOnClickListener { viewModel.share() }

        // --- Rating ---
        binding.ratingBar.setOnRatingBarChangeListener { _, rating, _ ->
            viewModel.rate(rating.toInt())
        }

        // --- Generate ---
        binding.btnGenerate.setOnClickListener {
            val topic = binding.generateInput.text.toString().trim()
            if (topic.isBlank()) {
                Snackbar.make(binding.root, R.string.enter_topic, Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            viewModel.generateJoke(topic)
        }

        // --- Quick Topics chips ---
        setupQuickTopics()

        // --- Observers ---
        viewModel.joke.observe(viewLifecycleOwner) { joke ->
            joke?.let {
                binding.jokeText.text = it.text
                binding.categoryChip.text = CatEmojis.withLabel(it.category)
                binding.ratingBar.rating = it.rating.toFloat()
            }
        }

        viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
        }

        viewModel.isGenerating.observe(viewLifecycleOwner) { generating ->
            if (generating) {
                binding.btnGenerate.text = getString(R.string.generating)
                binding.btnGenerate.isEnabled = false
            } else {
                binding.btnGenerate.text = getString(R.string.generate)
                binding.btnGenerate.isEnabled = true
            }
        }

        viewModel.error.observe(viewLifecycleOwner) { error ->
            error?.let {
                Toast.makeText(requireContext(), it, Toast.LENGTH_SHORT).show()
            }
        }

        viewModel.shareText.observe(viewLifecycleOwner) { text ->
            text?.let {
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, it)
                }
                startActivity(Intent.createChooser(intent, getString(R.string.share)))
            }
        }

        // --- Stats ---
        viewModel.stats.observe(viewLifecycleOwner) { stats ->
            stats?.let {
                binding.statsJokes.text = getString(R.string.stats_jokes, it.totalJokes)
                binding.statsCats.text = getString(R.string.stats_cats, it.categories)
            }
        }
    }

    private fun setupQuickTopics() {
        val chipGroup = binding.quickTopics
        chipGroup.removeAllViews()

        for ((label, category) in quickTopics) {
            val chip = Chip(requireContext()).apply {
                text = label
                isClickable = true
                isCheckable = true
                setChipBackgroundColorResource(R.color.surface_dark)
                setTextColor(resources.getColor(R.color.white, null))
                textSize = 12f
                id = View.generateViewId()
            }

            chip.setOnClickListener {
                if (selectedChipCategory == category) {
                    // Deselect — load random
                    selectedChipCategory = null
                    chip.isChecked = false
                    viewModel.loadRandom()
                } else {
                    selectedChipCategory = category
                    viewModel.loadRandomByCategory(category)
                }
            }

            chipGroup.addView(chip)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        ttsPlayer.release()
        _binding = null
    }
}
