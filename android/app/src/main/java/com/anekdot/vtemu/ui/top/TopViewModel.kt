package com.anekdot.vtemu.ui.top

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.repository.AnekdotRepository
import kotlinx.coroutines.launch

class TopViewModel(
    private val repository: AnekdotRepository
) : ViewModel() {

    private val _jokes = MutableLiveData<List<Joke>>()
    val jokes: LiveData<List<Joke>> = _jokes

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    init {
        loadTop()
    }

    fun loadTop(period: String = "day", count: Int = 20) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            when (val result = repository.getSocialTop(period, count)) {
                is ApiResponse.Success -> {
                    _jokes.value = result.data.jokes
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
