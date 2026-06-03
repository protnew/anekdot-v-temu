package com.anekdot.vtemu.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.CategoryJokes
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import kotlinx.coroutines.launch

class CategoriesViewModel(
    private val repository: AnekdotRepository
) : ViewModel() {

    private val _categories = MutableLiveData<List<String>>()
    val categories: LiveData<List<String>> = _categories

    private val _categoryJokes = MutableLiveData<List<Joke>>()
    val categoryJokes: LiveData<List<Joke>> = _categoryJokes

    private val _categoryJokesTotal = MutableLiveData(0)
    val categoryJokesTotal: LiveData<Int> = _categoryJokesTotal

    private val _selectedCategory = MutableLiveData<String?>()
    val selectedCategory: LiveData<String?> = _selectedCategory

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    init {
        loadCategories()
    }

    fun loadCategories() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            when (val result = repository.getCategories()) {
                is ApiResponse.Success -> {
                    _categories.value = result.data
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }

            _isLoading.value = false
        }
    }

    fun loadByCategory(name: String) {
        _selectedCategory.value = name
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            when (val result = repository.getJokesByCategory(name, 20)) {
                is ApiResponse.Success -> {
                    _categoryJokes.value = result.data.jokes
                    _categoryJokesTotal.value = result.data.total
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }

            _isLoading.value = false
        }
    }

    fun clearSelectedCategory() {
        _selectedCategory.value = null
        _categoryJokes.value = emptyList()
    }

    fun clearError() {
        _error.value = null
    }
}
