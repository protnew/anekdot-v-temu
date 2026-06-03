package com.anekdot.vtemu.ui.search

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
import com.anekdot.vtemu.AnekdotApp
import com.anekdot.vtemu.R
import com.anekdot.vtemu.audio.TtsPlayer
import com.anekdot.vtemu.databinding.FragmentSearchBinding
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.util.CatEmojis
import com.anekdot.vtemu.viewmodel.SearchViewModel
import com.anekdot.vtemu.viewmodel.ViewModelFactory
import com.google.android.material.snackbar.Snackbar

class SearchFragment : Fragment() {

    private var _binding: FragmentSearchBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: SearchViewModel
    private lateinit var adapter: JokesSearchAdapter
    private lateinit var ttsPlayer: TtsPlayer

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSearchBinding.inflate(inflater, container, false)
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

        viewModel = ViewModelProvider(this, factory)[SearchViewModel::class.java]
        ttsPlayer = TtsPlayer(requireContext())

        adapter = JokesSearchAdapter(
            onCopy = { joke -> copyToClipboard(joke) },
            onTts = { joke ->
                val baseUrl = anekdotApp.retrofit.baseUrl().toString()
                ttsPlayer.play(joke.text, baseUrl, repository)
            },
            onFav = { joke ->
                Snackbar.make(binding.root, "Добавлено в избранное", Snackbar.LENGTH_SHORT).show()
            }
        )
        binding.searchResults.layoutManager = LinearLayoutManager(requireContext())
        binding.searchResults.adapter = adapter

        binding.btnSearch.setOnClickListener {
            val query = binding.searchInput.text.toString().trim()
            if (query.isNotBlank()) {
                if (viewModel.isContextMode.value == true) {
                    viewModel.contextSearch(query)
                } else {
                    viewModel.search(query)
                }
            }
        }

        binding.chipContextMode.setOnClickListener {
            viewModel.toggleContextMode()
        }

        viewModel.searchResults.observe(viewLifecycleOwner) { jokes ->
            adapter.submitList(jokes)
            binding.emptyState.visibility = if (jokes.isEmpty()) View.VISIBLE else View.GONE
            binding.searchResults.visibility = if (jokes.isEmpty()) View.GONE else View.VISIBLE
        }

        viewModel.isContextMode.observe(viewLifecycleOwner) { isContext ->
            binding.chipContextMode.isChecked = isContext
            binding.searchInputLayout.hint = if (isContext) "Контекст разговора..." else "Тема для поиска..."
        }

        viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
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

class JokesSearchAdapter(
    private val onCopy: (Joke) -> Unit,
    private val onTts: (Joke) -> Unit,
    private val onFav: (Joke) -> Unit
) : androidx.recyclerview.widget.ListAdapter<Joke, JokeViewHolder>(JokeDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): JokeViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_joke, parent, false)
        return JokeViewHolder(view, onCopy, onTts, onFav)
    }

    override fun onBindViewHolder(holder: JokeViewHolder, position: Int) {
        holder.bind(currentList[position])
    }
}

class JokeViewHolder(
    view: View,
    private val onCopy: (Joke) -> Unit,
    private val onTts: (Joke) -> Unit,
    private val onFav: (Joke) -> Unit
) : androidx.recyclerview.widget.RecyclerView.ViewHolder(view) {

    fun bind(joke: Joke) {
        val chip = itemView.findViewById<com.google.android.material.chip.Chip>(R.id.category_chip)
        chip.text = CatEmojis.withLabel(joke.category)

        itemView.findViewById<android.widget.TextView>(R.id.joke_text).text = joke.text

        val ratingText = itemView.findViewById<android.widget.TextView>(R.id.rating_text)
        val sb = StringBuilder(String.format("%.1f", joke.rating))
        if (joke.semanticScore != null) {
            sb.append("  🎯").append((joke.semanticScore * 100).toInt()).append("%")
        }
        if (joke.generated) {
            sb.append("  🤖AI")
        }
        ratingText.text = sb.toString()

        // Badges
        val badgeSemantic = itemView.findViewById<android.widget.TextView>(R.id.badgeSemantic)
        if (joke.semanticScore != null) {
            badgeSemantic.visibility = View.VISIBLE
            badgeSemantic.text = "🎯 ${((joke.semanticScore * 100).toInt())}%"
        } else {
            badgeSemantic.visibility = View.GONE
        }

        val badgeGenerated = itemView.findViewById<android.widget.TextView>(R.id.badgeGenerated)
        badgeGenerated.visibility = if (joke.generated) View.VISIBLE else View.GONE

        // Action buttons
        itemView.findViewById<View>(R.id.btn_copy)?.setOnClickListener { onCopy(joke) }
        itemView.findViewById<View>(R.id.btn_tts_item)?.setOnClickListener { onTts(joke) }
        itemView.findViewById<View>(R.id.btn_fav)?.setOnClickListener { onFav(joke) }
    }
}

class JokeDiffCallback : androidx.recyclerview.widget.DiffUtil.ItemCallback<Joke>() {
    override fun areItemsTheSame(oldItem: Joke, newItem: Joke) = oldItem.id == newItem.id
    override fun areContentsTheSame(oldItem: Joke, newItem: Joke) = oldItem == newItem
}
