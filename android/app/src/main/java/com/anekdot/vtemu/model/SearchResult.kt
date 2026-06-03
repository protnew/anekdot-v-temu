package com.anekdot.vtemu.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class SearchResult(
    @Json(name = "jokes") val jokes: List<Joke> = emptyList(),
    @Json(name = "total") val total: Int = 0
)
