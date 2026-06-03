package com.anekdot.vtemu.ui.categories

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.GridLayoutManager
import com.anekdot.vtemu.R
import com.anekdot.vtemu.databinding.FragmentCategoriesBinding
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.viewmodel.CategoriesViewModel
import com.anekdot.vtemu.viewmodel.ViewModelFactory

class CategoriesFragment : Fragment() {

    private var _binding: FragmentCategoriesBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: CategoriesViewModel

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentCategoriesBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val factory = ViewModelFactory(AnekdotRepository(requireContext()))
        viewModel = ViewModelProvider(this, factory)[CategoriesViewModel::class.java]

        val adapter = CategoriesAdapter { category ->
            viewModel.loadByCategory(category)
        }
        binding.categoriesGrid.layoutManager = GridLayoutManager(requireContext(), 2)
        binding.categoriesGrid.adapter = adapter

        viewModel.categories.observe(viewLifecycleOwner) { categories ->
            adapter.submitList(categories)
        }

        viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
        }

        viewModel.error.observe(viewLifecycleOwner) { error ->
            error?.let { Toast.makeText(requireContext(), it, Toast.LENGTH_SHORT).show() }
        }

        viewModel.loadCategories()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

data class CategoryItem(val name: String, val count: Int)

class CategoriesAdapter(
    private val onClick: (String) -> Unit
) : androidx.recyclerview.widget.ListAdapter<CategoryItem, CategoryViewHolder>(CategoryDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CategoryViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_category, parent, false)
        return CategoryViewHolder(view, onClick)
    }

    override fun onBindViewHolder(holder: CategoryViewHolder, position: Int) {
        val item = currentList[position]
        holder.bind(item)
    }
}

class CategoryViewHolder(
    view: View,
    private val onClick: (String) -> Unit
) : androidx.recyclerview.widget.RecyclerView.ViewHolder(view) {

    fun bind(item: CategoryItem) {
        itemView.findViewById<android.widget.TextView>(R.id.category_name).text = item.name
        itemView.findViewById<android.widget.TextView>(R.id.joke_count).text =
            itemView.context.getString(R.string.joke_count, item.count)
        itemView.setOnClickListener { onClick(item.name) }
    }
}

class CategoryDiffCallback : androidx.recyclerview.widget.DiffUtil.ItemCallback<CategoryItem>() {
    override fun areItemsTheSame(oldItem: CategoryItem, newItem: CategoryItem) = oldItem.name == newItem.name
    override fun areContentsTheSame(oldItem: CategoryItem, newItem: CategoryItem) = oldItem == newItem
}
