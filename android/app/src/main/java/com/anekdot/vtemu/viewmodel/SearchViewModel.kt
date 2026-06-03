package com.anekdot.vtemu.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.ContextResult
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.model.SearchResult
import com.anekdot.vtemu.repository.AnekdotRepository
import kotlinx.coroutines.launch

class SearchViewModel(
    private val repository: AnekdotRepository
) : ViewModel() {

    private val _results = MutableLiveData<List<Joke>>()
    val results: LiveData<List<Joke>> = _results

    private val _totalResults = MutableLiveData(0)
    val totalResults: LiveData<Int> = _totalResults

    private val _matchedCategories = MutableLiveData<List<String>>()
    val matchedCategories: LiveData<List<String>> = _matchedCategories

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    private val _isContextMode = MutableLiveData(false)
    val isContextMode: LiveData<Boolean> = _isContextMode

    private val _generatedJoke = MutableLiveData<Joke?>()
    val generatedJoke: LiveData<Joke?> = _generatedJoke

    fun toggleContextMode() {
        _isContextMode.value = !(_isContextMode.value ?: false)
        _results.value = emptyList()
        _matchedCategories.value = emptyList()
        _generatedJoke.value = null
    }

    fun search(query: String) {
        if (query.isBlank()) return

        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            _generatedJoke.value = null

            if (_isContextMode.value == true) {
                // Context search mode
                when (val result = repository.contextSearch(query)) {
                    is ApiResponse.Success -> {
                        _results.value = result.data.jokes
                        _matchedCategories.value = result.data.matchedCategories
                    }
                    is ApiResponse.Error -> {
                        _error.value = result.message
                    }
                }
            } else {
                // Regular search mode
                when (val result = repository.searchJokes(query)) {
                    is ApiResponse.Success -> {
                        _results.value = result.data.jokes
                        _totalResults.value = result.data.total
                    }
                    is ApiResponse.Error -> {
                        _error.value = result.message
                    }
                }
            }

            _isLoading.value = false
        }
    }

    fun generateJoke(text: String) {
        if (text.isBlank()) return
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            when (val result = repository.generateJoke(text)) {
                is ApiResponse.Success -> {
                    _generatedJoke.value = result.data
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }

            _isLoading.value = false
        }
    }

    fun clearError() {
        _error.value = null
    }
}
