package com.anekdot.vtemu.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

// Request models

@JsonClass(generateAdapter = true)
data class ContextRequest(
    @Json(name = "text") val text: String,
    @Json(name = "count") val count: Int = 5
)

@JsonClass(generateAdapter = true)
data class GenerateRequest(
    @Json(name = "text") val text: String
)

@JsonClass(generateAdapter = true)
data class RateRequest(
    @Json(name = "joke_id") val jokeId: String,
    @Json(name = "rating") val rating: Int
)

@JsonClass(generateAdapter = true)
data class FavoriteRequest(
    @Json(name = "joke_id") val jokeId: String,
    @Json(name = "user_id") val userId: String
)

@JsonClass(generateAdapter = true)
data class UserJokeRequest(
    @Json(name = "text") val text: String,
    @Json(name = "category") val category: String,
    @Json(name = "tags") val tags: List<String> = emptyList()
)

@JsonClass(generateAdapter = true)
data class TtsRequest(
    @Json(name = "text") val text: String
)

@JsonClass(generateAdapter = true)
data class AliceRequest(
    @Json(name = "request") val request: String
)

// Response models

@JsonClass(generateAdapter = true)
data class LikeResult(
    @Json(name = "liked") val liked: Boolean = false
)

@JsonClass(generateAdapter = true)
data class RateResult(
    @Json(name = "new_rating") val newRating: Double = 0.0
)

@JsonClass(generateAdapter = true)
data class TtsResult(
    @Json(name = "audio_file") val audioFile: String = ""
)

@JsonClass(generateAdapter = true)
data class PersonalizeResult(
    @Json(name = "status") val status: String = ""
)

@JsonClass(generateAdapter = true)
data class AdResult(
    @Json(name = "ad") val ad: AdInfo? = null
)

@JsonClass(generateAdapter = true)
data class AdInfo(
    @Json(name = "show") val show: Boolean = false,
    @Json(name = "type") val type: String = "",
    @Json(name = "url") val url: String = ""
)

@JsonClass(generateAdapter = true)
data class PremiumResult(
    @Json(name = "available") val available: Boolean = false,
    @Json(name = "price") val price: String = "",
    @Json(name = "features") val features: List<String> = emptyList()
)

@JsonClass(generateAdapter = true)
data class AliceResponse(
    @Json(name = "response") val response: String = "",
    @Json(name = "joke") val joke: Joke? = null
)
