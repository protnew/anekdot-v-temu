package com.anekdot.vtemu.viewmodel

import android.content.Intent
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.Joke
import com.anekdot.vtemu.model.LikeResult
import com.anekdot.vtemu.model.RateResult
import com.anekdot.vtemu.model.TtsResult
import com.anekdot.vtemu.repository.AnekdotRepository
import kotlinx.coroutines.launch

class RandomViewModel(
    private val repository: AnekdotRepository
) : ViewModel() {

    private val _joke = MutableLiveData<Joke>()
    val joke: LiveData<Joke> = _joke

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    private val _liked = MutableLiveData<Boolean>()
    val liked: LiveData<Boolean> = _liked

    private val _newRating = MutableLiveData<Double>()
    val newRating: LiveData<Double> = _newRating

    private val _ttsAudioFile = MutableLiveData<String?>()
    val ttsAudioFile: LiveData<String?> = _ttsAudioFile

    private val _shareText = MutableLiveData<String?>()
    val shareText: LiveData<String?> = _shareText

    init {
        loadRandom()
    }

    fun loadRandom(category: String? = null) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            val result = if (category != null) {
                repository.getRandomJokeByCategory(category)
            } else {
                repository.getRandomJoke()
            }

            _isLoading.value = false
            when (result) {
                is ApiResponse.Success -> {
                    _joke.value = result.data
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }
        }
    }

    fun like() {
        val jokeId = _joke.value?.id ?: return
        viewModelScope.launch {
            when (val result = repository.likeJoke(jokeId)) {
                is ApiResponse.Success -> {
                    _liked.value = result.data.liked
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }
        }
    }

    fun rate(stars: Int) {
        val jokeId = _joke.value?.id ?: return
        viewModelScope.launch {
            when (val result = repository.rateJoke(jokeId, stars)) {
                is ApiResponse.Success -> {
                    _newRating.value = result.data.newRating
                    // Update local joke rating
                    _joke.value?.let { currentJoke ->
                        _joke.value = currentJoke.copy(rating = result.data.newRating)
                    }
                }
                is ApiResponse.Error -> {
                    _error.value = result.message
                }
            }
        }
    }

    fun share() {
        _joke.value?.let { joke ->
            _shareText.value = "${joke.text}\n\n— Анекдот в Тему"
        }
    }

    fun textToSpeech() {
        val text = _joke.value?.text ?: return
        viewModelScope.launch {
            when (val result = repository.textToSpeech(text)) {
                is ApiResponse.Success -> {
                    _ttsAudioFile.value = result.data.audioFile
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

    fun clearShareText() {
        _shareText.value = null
    }
}
