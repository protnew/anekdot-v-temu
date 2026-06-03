// Top-level build file
plugins {
    id("com.android.application") version "8.2.2" apply false
    id("com.android.library") version "8.2.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
    id("androidx.navigation.safeargs.kotlin") version "2.7.7" apply false
}

extra.apply {
    set("kotlin_version", "1.9.22")
    set("nav_version", "2.7.7")
    set("retrofit_version", "2.9.0")
    set("moshi_version", "1.15.1")
    set("glide_version", "4.16.0")
    set("coroutines_version", "1.7.3")
    set("lifecycle_version", "2.7.0")
    set("material3_version", "1.11.0")
}
