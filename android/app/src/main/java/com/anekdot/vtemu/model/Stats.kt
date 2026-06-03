package com.anekdot.vtemu.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Stats(
    @Json(name = "total_jokes") val totalJokes: Int = 0,
    @Json(name = "categories") val categories: Int = 0,
    @Json(name = "avg_rating") val avgRating: Double = 0.0,
    @Json(name = "version") val version: String = "",
    @Json(name = "en_jokes") val enJokes: Int = 0,
    @Json(name = "features") val features: List<String> = emptyList()
)
