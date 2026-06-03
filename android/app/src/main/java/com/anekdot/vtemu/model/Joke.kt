package com.anekdot.vtemu.model

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Joke(
    @Json(name = "id") val id: Int,
    @Json(name = "text") val text: String,
    @Json(name = "category") val category: String,
    @Json(name = "rating") val rating: Double = 4.0,
    @Json(name = "tags") val tags: List<String> = emptyList(),
    @Json(name = "likes") val likes: Int = 0,
    @Json(name = "views") val views: Int = 0,
    @Json(name = "generated") val generated: Boolean = false,
    @Json(name = "generator") val generator: String? = null,
    @Json(name = "semantic_score") val semanticScore: Double? = null
)

@JsonClass(generateAdapter = true)
data class StatsResponse(
    @Json(name = "total_jokes") val totalJokes: Int,
    @Json(name = "en_jokes") val enJokes: Int,
    @Json(name = "categories") val categories: Int,
    @Json(name = "favorites_count") val favoritesCount: Int,
    @Json(name = "history_count") val historyCount: Int,
    @Json(name = "avg_rating") val avgRating: Double,
    @Json(name = "vocabulary_size") val vocabularySize: Int,
    @Json(name = "version") val version: String
)

@JsonClass(generateAdapter = true)
data class JokesResponse(
    @Json(name = "jokes") val jokes: List<Joke>,
    @Json(name = "total") val total: Int
)

@JsonClass(generateAdapter = true)
data class ContextRequest(
    @Json(name = "text") val text: String,
    @Json(name = "count") val count: Int = 3,
    @Json(name = "category") val category: String? = null
)

@JsonClass(generateAdapter = true)
data class ContextResponse(
    @Json(name = "jokes") val jokes: List<Joke>,
    @Json(name = "matched_categories") val matchedCategories: List<String>,
    @Json(name = "context") val context: String,
    @Json(name = "search_method") val searchMethod: String
)

@JsonClass(generateAdapter = true)
data class GenerateRequest(
    @Json(name = "text") val text: String,
    @Json(name = "count") val count: Int = 1,
    @Json(name = "category") val category: String? = null
)

@JsonClass(generateAdapter = true)
data class GenerateResponse(
    @Json(name = "joke") val joke: Joke,
    @Json(name = "matched_categories") val matchedCategories: List<String>
)

@JsonClass(generateAdapter = true)
data class FavoriteRequest(
    @Json(name = "joke_id") val jokeId: Int,
    @Json(name = "user_id") val userId: String = "default"
)

@JsonClass(generateAdapter = true)
data class FavoritesResponse(
    @Json(name = "jokes") val jokes: List<Joke>
)

@JsonClass(generateAdapter = true)
data class FavoriteIdsResponse(
    @Json(name = "favorites") val favorites: List<Int>
)

@JsonClass(generateAdapter = true)
data class RatingRequest(
    @Json(name = "joke_id") val jokeId: Int,
    @Json(name = "rating") val rating: Double
)

@JsonClass(generateAdapter = true)
data class RatingResponse(
    @Json(name = "new_rating") val newRating: Double
)

@JsonClass(generateAdapter = true)
data class LikeResponse(
    @Json(name = "liked") val liked: Boolean
)

@JsonClass(generateAdapter = true)
data class UserJokeRequest(
    @Json(name = "category") val category: String,
    @Json(name = "text") val text: String,
    @Json(name = "tags") val tags: List<String> = emptyList()
)

@JsonClass(generateAdapter = true)
data class UserJokeResponse(
    @Json(name = "id") val id: Int,
    @Json(name = "status") val status: String
)

@JsonClass(generateAdapter = true)
data class UserJokesResponse(
    @Json(name = "jokes") val jokes: List<UserJoke>
)

@JsonClass(generateAdapter = true)
data class UserJoke(
    @Json(name = "id") val id: Int,
    @Json(name = "user_id") val userId: String,
    @Json(name = "category") val category: String,
    @Json(name = "text") val text: String,
    @Json(name = "rating") val rating: Double = 4.0,
    @Json(name = "tags") val tags: List<String> = emptyList(),
    @Json(name = "approved") val approved: Int = 0
)

@JsonClass(generateAdapter = true)
data class DeleteResponse(
    @Json(name = "deleted") val deleted: Boolean
)

@JsonClass(generateAdapter = true)
data class SocialTopResponse(
    @Json(name = "jokes") val jokes: List<Joke>,
    @Json(name = "period") val period: String
)

@JsonClass(generateAdapter = true)
data class TtsRequest(
    @Json(name = "text") val text: String
)

@JsonClass(generateAdapter = true)
data class TtsResponse(
    @Json(name = "text") val text: String,
    @Json(name = "audio_file") val audioFile: String,
    @Json(name = "duration_estimate") val durationEstimate: String,
    @Json(name = "generator") val generator: String
)

@JsonClass(generateAdapter = true)
data class PersonalizeResponse(
    @Json(name = "status") val status: String
)

@JsonClass(generateAdapter = true)
data class PersonalizedJokesResponse(
    @Json(name = "jokes") val jokes: List<Joke>
)

@JsonClass(generateAdapter = true)
data class AnalyticsStatsResponse(
    @Json(name = "total_events") val totalEvents: Int,
    @Json(name = "unique_users") val uniqueUsers: Int,
    @Json(name = "top_categories") val topCategories: List<CategoryCount>
)

@JsonClass(generateAdapter = true)
data class CategoryCount(
    @Json(name = "category") val category: String?,
    @Json(name = "cnt") val count: Int
)

@JsonClass(generateAdapter = true)
data class PopularResponse(
    @Json(name = "popular") val popular: List<CategoryCount>,
    @Json(name = "period_days") val periodDays: Int
)

@JsonClass(generateAdapter = true)
data class AdResponse(
    @Json(name = "ad") val ad: AdInfo
)

@JsonClass(generateAdapter = true)
data class AdInfo(
    @Json(name = "type") val type: String,
    @Json(name = "text") val text: String,
    @Json(name = "link") val link: String,
    @Json(name = "show") val show: Boolean
)

@JsonClass(generateAdapter = true)
data class PremiumResponse(
    @Json(name = "is_premium") val isPremium: Boolean,
    @Json(name = "features") val features: List<String>,
    @Json(name = "price") val price: String
)

@JsonClass(generateAdapter = true)
data class CategoriesResponse(
    @Json(name = "categories") val categories: Map<String, Int>
)

@JsonClass(generateAdapter = true)
data class ErrorResponse(
    @Json(name = "detail") val detail: String
)
