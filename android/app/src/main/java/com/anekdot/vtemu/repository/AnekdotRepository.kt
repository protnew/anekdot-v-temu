package com.anekdot.vtemu.repository

import com.anekdot.vtemu.api.AnekdotApi
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.*
import kotlinx.coroutines.delay
import retrofit2.HttpException

class AnekdotRepository(
    private val api: AnekdotApi,
    private val maxRetries: Int = 3,
    private val retryDelayMs: Long = 1000
) {

    // ============================================================
    // Core API wrappers returning ApiResponse
    // ============================================================

    suspend fun getStats(): ApiResponse<StatsResponse> = safeCall { api.getStats() }

    suspend fun getCategories(): ApiResponse<List<String>> = safeCall {
        val map = api.getCategories()
        map.keys.toList()
    }

    suspend fun getRandomJoke(): ApiResponse<Joke> = safeCallWithRetry { api.getRandomJoke() }

    suspend fun getRandomJokeByCategory(category: String): ApiResponse<Joke> = safeCallWithRetry {
        val response = api.getJokes(category = category, count = 1, randomize = true)
        response.jokes.first()
    }

    suspend fun getJokesByCategory(category: String, count: Int = 20): ApiResponse<JokesResponse> = safeCall {
        api.getJokes(category = category, count = count)
    }

    suspend fun searchJokes(query: String, limit: Int = 10): ApiResponse<JokesResponse> =
        safeCallWithRetry { api.searchJokes(query, limit) }

    suspend fun contextSearch(query: String): ApiResponse<ContextResponse> =
        safeCallWithRetry { api.contextJoke(ContextRequest(query)) }

    suspend fun contextJoke(text: String, count: Int = 3): ApiResponse<ContextResponse> =
        safeCallWithRetry { api.contextJoke(ContextRequest(text, count)) }

    suspend fun generateJoke(text: String): ApiResponse<GenerateResponse> =
        safeCall { api.generateJoke(GenerateRequest(text)) }

    suspend fun addFavorite(jokeId: String, userId: String): ApiResponse<FavoriteIdsResponse> =
        safeCall { api.addFavorite(FavoriteRequest(jokeId, userId)) }

    suspend fun addFavorite(jokeId: Int, userId: String = "default"): ApiResponse<FavoriteIdsResponse> =
        safeCall { api.addFavorite(FavoriteRequest(jokeId.toString(), userId)) }

    suspend fun getFavorites(userId: String): ApiResponse<FavoritesResponse> =
        safeCall { api.getFavorites(userId) }

    suspend fun removeFavorite(jokeId: String, userId: String): ApiResponse<FavoriteIdsResponse> =
        safeCall { api.removeFavorite(jokeId.toInt(), userId) }

    suspend fun removeFavorite(jokeId: Int, userId: String = "default"): ApiResponse<FavoriteIdsResponse> =
        safeCall { api.removeFavorite(jokeId, userId) }

    suspend fun rateJoke(jokeId: Int, rating: Int): ApiResponse<RatingResponse> =
        safeCall { api.rateJoke(RatingRequest(jokeId.toString(), rating)) }

    suspend fun rateJoke(jokeId: Int, rating: Double): ApiResponse<RatingResponse> =
        safeCall { api.rateJoke(RatingRequest(jokeId.toString(), rating.toInt())) }

    suspend fun likeJoke(jokeId: Int): ApiResponse<LikeResponse> =
        safeCall { api.likeJoke(jokeId) }

    suspend fun createUserJoke(category: String, text: String, tags: List<String> = emptyList()): ApiResponse<UserJokeResponse> =
        safeCall { api.createUserJoke(UserJokeRequest(text, category, tags)) }

    suspend fun getUserJokes(approved: Int = 0): ApiResponse<UserJokesResponse> =
        safeCall { api.getUserJokes(approved) }

    suspend fun deleteUserJoke(jokeId: Int): ApiResponse<DeleteResponse> =
        safeCall { api.deleteUserJoke(jokeId) }

    suspend fun getEnglishJokes(count: Int = 5): ApiResponse<JokesResponse> =
        safeCall { api.getEnglishJokes(count) }

    suspend fun getSocialTop(period: String = "day", count: Int = 10): ApiResponse<SocialTopResponse> =
        safeCall { api.getSocialTop(period, count) }

    suspend fun textToSpeech(text: String): ApiResponse<TtsResponse> =
        safeCall { api.textToSpeech(TtsRequest(text)) }

    suspend fun getPersonalized(userHash: String, count: Int = 3): ApiResponse<PersonalizedJokesResponse> =
        safeCall { api.getPersonalized(userHash, count) }

    suspend fun updatePreferences(userHash: String, likedCat: String, dislikedCat: String): ApiResponse<PersonalizeResponse> =
        safeCall { api.updatePreferences(userHash, likedCat, dislikedCat) }

    suspend fun getAnalyticsStats(): ApiResponse<AnalyticsStatsResponse> =
        safeCall { api.getAnalyticsStats() }

    suspend fun getPopularTopics(days: Int = 7): ApiResponse<PopularResponse> =
        safeCall { api.getPopularTopics(days) }

    suspend fun getAd(): ApiResponse<AdResponse> =
        safeCall { api.getAd() }

    suspend fun getPremiumStatus(userHash: String = ""): ApiResponse<PremiumResponse> =
        safeCall { api.getPremiumStatus(userHash) }

    // ============================================================
    // Safe call wrappers
    // ============================================================

    private suspend fun <T> safeCall(call: suspend () -> T): ApiResponse<T> {
        return try {
            ApiResponse.success(call())
        } catch (e: HttpException) {
            ApiResponse.error(e.message ?: "HTTP ${e.code()}", e.code())
        } catch (e: Exception) {
            ApiResponse.error(e.message ?: "Unknown error")
        }
    }

    private suspend fun <T> safeCallWithRetry(call: suspend () -> T): ApiResponse<T> {
        var lastException: Exception? = null
        repeat(maxRetries) { attempt ->
            try {
                return ApiResponse.success(call())
            } catch (e: HttpException) {
                if (e.code() in 400..499) {
                    return ApiResponse.error(e.message ?: "HTTP ${e.code()}", e.code())
                }
                lastException = e
            } catch (e: Exception) {
                lastException = e
            }
            if (attempt < maxRetries - 1) {
                delay(retryDelayMs * (attempt + 1))
            }
        }
        return ApiResponse.error(lastException?.message ?: "Unknown error")
    }
}
