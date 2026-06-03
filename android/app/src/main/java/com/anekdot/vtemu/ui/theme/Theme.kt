package com.anekdot.vtemu.ui.theme

import android.app.Activity
import android.os.Build
import androidx.annotation.RequiresApi
import androidx.appcompat.app.AppCompatDelegate

object ThemeHelper {

    fun applyDarkTheme() {
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
    }

    fun isDarkTheme(): Boolean {
        return true // Always dark in this app
    }
}
