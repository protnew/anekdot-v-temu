package com.anekdot.vtemu.api

import com.anekdot.vtemu.model.*
import retrofit2.Response
import retrofit2.http.*

interface AnekdotApi {

    @GET("api/stats")
    suspend fun getStats(): StatsResponse

    @GET("api/categories")
    suspend fun getCategories(): Map<String, Int>

    @GET("api/jokes")
    suspend fun getJokes(
        @Query("category") category: String? = null,
        @Query("count") count: Int = 5,
        @Query("randomize") randomize: Boolean = true
    ): JokesResponse

    @GET("api/joke/random")
    suspend fun getRandomJoke(): Joke

    @GET("api/jokes/search")
    suspend fun searchJokes(
        @Query("q") query: String,
        @Query("limit") limit: Int = 10
    ): JokesResponse

    @POST("api/jokes/context")
    suspend fun contextJoke(@Body request: ContextRequest): ContextResponse

    @POST("api/jokes/generate")
    suspend fun generateJoke(@Body request: GenerateRequest): GenerateResponse

    @POST("api/favorites")
    suspend fun addFavorite(@Body request: FavoriteRequest): FavoriteIdsResponse

    @GET("api/favorites")
    suspend fun getFavorites(@Query("user_id") userId: String = "default"): FavoritesResponse

    @DELETE("api/favorites/{joke_id}")
    suspend fun removeFavorite(
        @Path("joke_id") jokeId: Int,
        @Query("user_id") userId: String = "default"
    ): FavoriteIdsResponse

    @POST("api/rate")
    suspend fun rateJoke(@Body request: RateRequest): RatingResponse

    @POST("api/jokes/{joke_id}/like")
    suspend fun likeJoke(@Path("joke_id") jokeId: Int): LikeResponse

    @POST("api/user-jokes")
    suspend fun createUserJoke(@Body request: UserJokeRequest): UserJokeResponse

    @GET("api/user-jokes")
    suspend fun getUserJokes(@Query("approved") approved: Int = 0): UserJokesResponse

    @DELETE("api/user-jokes/{joke_id}")
    suspend fun deleteUserJoke(@Path("joke_id") jokeId: Int): DeleteResponse

    @GET("api/jokes/en")
    suspend fun getEnglishJokes(@Query("count") count: Int = 5): JokesResponse

    @GET("api/jokes/social/top")
    suspend fun getSocialTop(
        @Query("period") period: String = "day",
        @Query("count") count: Int = 10
    ): SocialTopResponse

    @POST("api/voice/tts")
    suspend fun textToSpeech(@Body request: TtsRequest): TtsResponse

    @POST("api/personalize/{user_hash}")
    suspend fun updatePreferences(
        @Path("user_hash") userHash: String,
        @Query("liked_cat") likedCat: String = "",
        @Query("disliked_cat") dislikedCat: String = ""
    ): PersonalizeResponse

    @GET("api/personalize/{user_hash}")
    suspend fun getPersonalized(
        @Path("user_hash") userHash: String,
        @Query("count") count: Int = 3
    ): PersonalizedJokesResponse

    @GET("api/analytics/stats")
    suspend fun getAnalyticsStats(): AnalyticsStatsResponse

    @GET("api/analytics/popular")
    suspend fun getPopularTopics(@Query("days") days: Int = 7): PopularResponse

    @GET("api/monetization/ad")
    suspend fun getAd(): AdResponse

    @GET("api/monetization/premium")
    suspend fun getPremiumStatus(@Query("user_hash") userHash: String = ""): PremiumResponse

    // Raw Response versions for error handling
    @GET("api/joke/random")
    suspend fun getRandomJokeRaw(): Response<Joke>

    @POST("api/rate")
    suspend fun rateJokeRaw(@Body request: RateRequest): Response<RatingResponse>

    @POST("api/jokes/context")
    suspend fun contextJokeRaw(@Body request: ContextRequest): Response<ContextResponse>

    @POST("api/jokes/generate")
    suspend fun generateJokeRaw(@Body request: GenerateRequest): Response<GenerateResponse>

    @GET("api/jokes/search")
    suspend fun searchJokesRaw(
        @Query("q") query: String,
        @Query("limit") limit: Int = 10
    ): Response<JokesResponse>
}
