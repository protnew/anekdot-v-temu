package com.anekdot.vtemu.ui.random

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.anekdot.vtemu.R
import com.anekdot.vtemu.databinding.FragmentRandomBinding
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.viewmodel.RandomViewModel
import com.anekdot.vtemu.viewmodel.ViewModelFactory

class RandomFragment : Fragment() {

    private var _binding: FragmentRandomBinding? = null
    private val binding get() = _binding!!
    private lateinit var viewModel: RandomViewModel

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentRandomBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val factory = ViewModelFactory(AnekdotRepository(requireContext()))
        viewModel = ViewModelProvider(this, factory)[RandomViewModel::class.java]

        binding.fabRefresh.setOnClickListener { viewModel.loadRandom() }
        binding.btnLike.setOnClickListener { viewModel.like() }
        binding.btnTts.setOnClickListener { viewModel.tts() }
        binding.btnShare.setOnClickListener { viewModel.share() }
        binding.ratingBar.setOnRatingBarChangeListener { _, rating, _ ->
            viewModel.rate(rating.toInt())
        }

        viewModel.joke.observe(viewLifecycleOwner) { joke ->
            joke?.let {
                binding.jokeText.text = it.text
                binding.categoryChip.text = it.category
                binding.ratingBar.rating = (it.rating ?: 0f)
            }
        }

        viewModel.isLoading.observe(viewLifecycleOwner) { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
        }

        viewModel.error.observe(viewLifecycleOwner) { error ->
            error?.let {
                Toast.makeText(requireContext(), it, Toast.LENGTH_SHORT).show()
            }
        }

        viewModel.shareEvent.observe(viewLifecycleOwner) { text ->
            text?.let {
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, it)
                }
                startActivity(Intent.createChooser(intent, getString(R.string.share)))
            }
        }

        viewModel.loadRandom()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
