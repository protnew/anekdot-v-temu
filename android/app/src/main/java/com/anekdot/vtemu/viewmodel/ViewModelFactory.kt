package com.anekdot.vtemu.viewmodel

import android.content.SharedPreferences
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.anekdot.vtemu.repository.AnekdotRepository
import com.anekdot.vtemu.ui.top.TopViewModel

class ViewModelFactory(
    private val repository: AnekdotRepository,
    private val sharedPreferences: SharedPreferences
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return when (modelClass) {
            RandomViewModel::class.java -> RandomViewModel(repository) as T
            SearchViewModel::class.java -> SearchViewModel(repository) as T
            CategoriesViewModel::class.java -> CategoriesViewModel(repository) as T
            TopViewModel::class.java -> TopViewModel(repository) as T
            FavoritesViewModel::class.java -> {
                val userId = getUserId()
                FavoritesViewModel(repository, userId) as T
            }
            else -> throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
        }
    }

    fun getUserId(): String {
        var userId = sharedPreferences.getString("user_id", null)
        if (userId == null) {
            userId = java.util.UUID.randomUUID().toString()
            sharedPreferences.edit().putString("user_id", userId).apply()
        }
        return userId
    }
}
