package com.anekdot.vtemu.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ContextResult(
    @Json(name = "jokes") val jokes: List<Joke> = emptyList(),
    @Json(name = "matched_categories") val matchedCategories: List<String> = emptyList()
)
