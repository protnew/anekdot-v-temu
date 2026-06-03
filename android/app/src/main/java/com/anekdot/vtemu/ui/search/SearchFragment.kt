package com.anekdot.vtemu.ui.search

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.anekdot.vtemu.databinding.FragmentSearchBinding
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.viewmodel.SearchViewModel
import com.anekdot.vtemu.viewmodel.ViewModelFactory

class SearchFragment : Fragment() {

    private var _binding: FragmentSearchBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: SearchViewModel
    private lateinit var adapter: JokesSearchAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSearchBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val factory = ViewModelFactory(AnekdotRepository(requireContext()))
        viewModel = ViewModelProvider(this, factory)[SearchViewModel::class.java]

        adapter = JokesSearchAdapter()
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

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

class JokesSearchAdapter : androidx.recyclerview.widget.ListAdapter<Joke, androidx.recyclerview.widget.RecyclerView.ViewHolder>(JokeDiffCallback()) {
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): androidx.recyclerview.widget.RecyclerView.ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_joke, parent, false)
        return JokeViewHolder(view)
    }

    override fun onBindViewHolder(holder: androidx.recyclerview.widget.RecyclerView.ViewHolder, position: Int) {
        val joke = currentList[position]
        holder.itemView.findViewById<com.google.android.material.chip.Chip>(R.id.category_chip).text = joke.category
        holder.itemView.findViewById<android.widget.TextView>(R.id.joke_text).text = joke.text
        holder.itemView.findViewById<android.widget.TextView>(R.id.rating_text)?.text = String.format("%.1f", joke.rating ?: 0f)
    }
}

class JokeDiffCallback : androidx.recyclerview.widget.DiffUtil.ItemCallback<Joke>() {
    override fun areItemsTheSame(oldItem: Joke, newItem: Joke) = oldItem.id == newItem.id
    override fun areContentsTheSame(oldItem: Joke, newItem: Joke) = oldItem == newItem
}

class JokeViewHolder(view: View) : androidx.recyclerview.widget.RecyclerView.ViewHolder(view)
