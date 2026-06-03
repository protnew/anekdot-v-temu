package com.anekdot.vtemu.ui.top

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.anekdot.vtemu.R
import com.anekdot.vtemu.audio.TtsPlayer
import com.anekdot.vtemu.databinding.FragmentTopBinding
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.util.CatEmojis
import com.anekdot.vtemu.viewmodel.ViewModelFactory
import com.google.android.material.snackbar.Snackbar

class TopFragment : Fragment() {

    private var _binding: FragmentTopBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: TopViewModel
    private lateinit var adapter: TopJokesAdapter
    private lateinit var ttsPlayer: TtsPlayer

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentTopBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val app = requireActivity().application
        val anekdotApp = com.anekdot.vtemu.AnekdotApp.getInstance(app)
        val api = anekdotApp.anekdotApi
        val repository = AnekdotRepository(api)
        val prefs = requireActivity().getSharedPreferences("anekdot_prefs", Context.MODE_PRIVATE)
        val factory = ViewModelFactory(repository, prefs)

        viewModel = ViewModelProvider(this, factory)[TopViewModel::class.java]
        ttsPlayer = TtsPlayer(requireContext())

        adapter = TopJokesAdapter(
            onCopy = { joke -> copyToClipboard(joke) },
            onTts = { joke ->
                val baseUrl = anekdotApp.retrofit.baseUrl().toString()
                ttsPlayer.play(joke.text, baseUrl, repository)
            },
            onFav = { joke -> Toast.makeText(requireContext(), "Добавлено в избранное", Toast.LENGTH_SHORT).show() }
        )

        binding.topList.layoutManager = LinearLayoutManager(requireContext())
        binding.topList.adapter = adapter

        binding.swipeRefresh.setColorSchemeResources(R.color.accent_purple)
        binding.swipeRefresh.setOnRefreshListener {
            viewModel.loadTop()
        }

        viewModel.jokes.observe(viewLifecycleOwner) { jokes ->
            adapter.submitList(jokes)
            binding.emptyState.visibility = if (jokes.isEmpty()) View.VISIBLE else View.GONE
            binding.topList.visibility = if (jokes.isEmpty()) View.GONE else View.VISIBLE
        }

        viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
            binding.progressBar.visibility = if (loading && !binding.swipeRefresh.isRefreshing) View.VISIBLE else View.GONE
            if (!loading) binding.swipeRefresh.isRefreshing = false
        }

        viewModel.error.observe(viewLifecycleOwner) { error ->
            error?.let { Toast.makeText(requireContext(), it, Toast.LENGTH_SHORT).show() }
        }
    }

    private fun copyToClipboard(joke: Joke) {
        val clipboard = requireContext().getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText("joke", joke.text))
        Snackbar.make(binding.root, R.string.copied, Snackbar.LENGTH_SHORT).show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        ttsPlayer.release()
        _binding = null
    }
}

class TopJokesAdapter(
    private val onCopy: (Joke) -> Unit,
    private val onTts: (Joke) -> Unit,
    private val onFav: (Joke) -> Unit
) : androidx.recyclerview.widget.ListAdapter<Joke, TopJokeViewHolder>(TopDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TopJokeViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_joke, parent, false)
        return TopJokeViewHolder(view, onCopy, onTts, onFav)
    }

    override fun onBindViewHolder(holder: TopJokeViewHolder, position: Int) {
        holder.bind(currentList[position], position + 1)
    }
}

class TopJokeViewHolder(
    view: View,
    private val onCopy: (Joke) -> Unit,
    private val onTts: (Joke) -> Unit,
    private val onFav: (Joke) -> Unit
) : androidx.recyclerview.widget.RecyclerView.ViewHolder(view) {

    fun bind(joke: Joke, rank: Int) {
        val chip = itemView.findViewById<com.google.android.material.chip.Chip>(R.id.category_chip)
        chip.text = CatEmojis.withLabel(joke.category)

        itemView.findViewById<android.widget.TextView>(R.id.joke_text).text = joke.text

        val ratingText = itemView.findViewById<android.widget.TextView>(R.id.rating_text)
        val sb = StringBuilder()
        sb.append("#$rank  ")
        sb.append(String.format("%.1f", joke.rating))
        if (joke.semanticScore != null) {
            sb.append("  🎯").append((joke.semanticScore * 100).toInt()).append("%")
        }
        if (joke.generated) {
            sb.append("  🤖AI")
        }
        ratingText.text = sb.toString()

        // Action buttons
        itemView.findViewById<View>(R.id.btn_copy)?.setOnClickListener { onCopy(joke) }
        itemView.findViewById<View>(R.id.btn_tts_item)?.setOnClickListener { onTts(joke) }
        itemView.findViewById<View>(R.id.btn_fav)?.setOnClickListener { onFav(joke) }
    }
}

class TopDiffCallback : androidx.recyclerview.widget.DiffUtil.ItemCallback<Joke>() {
    override fun areItemsTheSame(oldItem: Joke, newItem: Joke) = oldItem.id == newItem.id
    override fun areContentsTheSame(oldItem: Joke, newItem: Joke) = oldItem == newItem
}
