package com.anekdot.vtemu.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import kotlinx.coroutines.launch

class FavoritesViewModel(
    private val repository: AnekdotRepository,
    private val userId: String
) : ViewModel() {

    private val _favorites = MutableLiveData<List<Joke>>()
    val favorites: LiveData<List<Joke>> = _favorites

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    private val _isEmpty = MutableLiveData(true)
    val isEmpty: LiveData<Boolean> = _isEmpty

    init {
        loadFavorites()
    }

    fun loadFavorites() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            when (val result = repository.getFavorites(userId)) {
                is ApiResponse.Success -> {
                    val jokes = result.data.jokes
                    _favorites.value = jokes
                    _isEmpty.value = jokes.isEmpty()
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                    _isEmpty.value = true
                }
            }

            _isLoading.value = false
        }
    }

    fun removeFavorite(jokeId: Int) {
        viewModelScope.launch {
            when (val result = repository.removeFavorite(jokeId, userId)) {
                is ApiResponse.Success -> {
                    // Remove from local list immediately
                    _favorites.value = _favorites.value?.filter { it.id != jokeId } ?: emptyList()
                    _isEmpty.value = _favorites.value?.isEmpty() ?: true
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }
        }
    }

    fun addFavorite(jokeId: Int) {
        viewModelScope.launch {
            when (val result = repository.addFavorite(jokeId, userId)) {
                is ApiResponse.Success -> {
                    loadFavorites() // Refresh
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }
        }
    }

    fun clearError() {
        _error.value = null
    }
}
