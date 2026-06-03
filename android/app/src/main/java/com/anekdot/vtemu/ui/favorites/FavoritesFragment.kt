package com.anekdot.vtemu.ui.favorites

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.ItemTouchHelper
import androidx.recyclerview.widget.LinearLayoutManager
import com.anekdot.vtemu.R
import com.anekdot.vtemu.databinding.FragmentFavoritesBinding
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.viewmodel.FavoritesViewModel
import com.anekdot.vtemu.viewmodel.ViewModelFactory

class FavoritesFragment : Fragment() {

    private var _binding: FragmentFavoritesBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: FavoritesViewModel

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentFavoritesBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val factory = ViewModelFactory(AnekdotRepository(requireContext()))
        viewModel = ViewModelProvider(this, factory)[FavoritesViewModel::class.java]

        val adapter = FavoritesAdapter { jokeId ->
            viewModel.removeFavorite(jokeId)
        }
        binding.favoritesList.layoutManager = LinearLayoutManager(requireContext())
        binding.favoritesList.adapter = adapter

        // Swipe to delete
        ItemTouchHelper(object : ItemTouchHelper.SimpleCallback(0, ItemTouchHelper.LEFT) {
            override fun onMove(rv: androidx.recyclerview.widget.RecyclerView,
                                vh: androidx.recyclerview.widget.RecyclerView.ViewHolder,
                                target: androidx.recyclerview.widget.RecyclerView.ViewHolder) = false
            override fun onSwiped(vh: androidx.recyclerview.widget.RecyclerView.ViewHolder, direction: Int) {
                val pos = vh.adapterPosition
                val joke = adapter.currentList[pos]
                viewModel.removeFavorite(joke.id)
            }
        }).attachToRecyclerView(binding.favoritesList)

        viewModel.favorites.observe(viewLifecycleOwner) { jokes ->
            adapter.submitList(jokes)
            binding.emptyState.visibility = if (jokes.isEmpty()) View.VISIBLE else View.GONE
            binding.favoritesList.visibility = if (jokes.isEmpty()) View.GONE else View.VISIBLE
        }

        viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
        }

        viewModel.error.observe(viewLifecycleOwner) { error ->
            error?.let { Toast.makeText(requireContext(), it, Toast.LENGTH_SHORT).show() }
        }

        viewModel.loadFavorites()
    }

    override fun onResume() {
        super.onResume()
        if (::viewModel.isInitialized) viewModel.loadFavorites()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

class FavoritesAdapter(
    private val onDelete: (Int) -> Unit
) : androidx.recyclerview.widget.ListAdapter<Joke, FavoriteViewHolder>(FavDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FavoriteViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_joke, parent, false)
        return FavoriteViewHolder(view)
    }

    override fun onBindViewHolder(holder: FavoriteViewHolder, position: Int) {
        val joke = currentList[position]
        holder.itemView.findViewById<com.google.android.material.chip.Chip>(R.id.category_chip).text = joke.category
        holder.itemView.findViewById<android.widget.TextView>(R.id.joke_text).text = joke.text
        holder.itemView.findViewById<android.widget.TextView>(R.id.rating_text)?.text =
            String.format("%.1f", joke.rating ?: 0f)
    }
}

class FavoriteViewHolder(view: View) : androidx.recyclerview.widget.RecyclerView.ViewHolder(view)

class FavDiffCallback : androidx.recyclerview.widget.DiffUtil.ItemCallback<Joke>() {
    override fun areItemsTheSame(oldItem: Joke, newItem: Joke) = oldItem.id == newItem.id
    override fun areContentsTheSame(oldItem: Joke, newItem: Joke) = oldItem == newItem
}
