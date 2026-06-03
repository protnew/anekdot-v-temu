package com.anekdot.vtemu.api

import com.anekdot.vtemu.model.*
import com.anekdot.vtemu.util.MockServer
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Before
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Retrofit
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import retrofit2.converter.moshi.MoshiConverterFactory

class AnekdotApiTest {

    private lateinit var server: MockWebServer
    private lateinit var api: AnekdotApi

    @Before
    fun setUp() {
        server = MockServer.createMockWebServer()
        server.start()
        api = MockServer.createApi(server)
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    // ============================================================
    // 1. Stats endpoint
    // ============================================================
    @Test
    fun `stats returns total_jokes 112360`() = runTest {
        val stats = api.getStats()
        assertThat(stats.totalJokes).isEqualTo(112360)
    }

    @Test
    fun `stats returns 41 categories`() = runTest {
        val stats = api.getStats()
        assertThat(stats.categories).isEqualTo(41)
    }

    @Test
    fun `stats returns version 3_5_0`() = runTest {
        val stats = api.getStats()
        assertThat(stats.version).isEqualTo("3.5.0")
    }

    @Test
    fun `stats returns avg_rating greater than zero`() = runTest {
        val stats = api.getStats()
        assertThat(stats.avgRating).isGreaterThan(0.0)
    }

    // ============================================================
    // 2. Categories endpoint
    // ============================================================
    @Test
    fun `categories returns map with 41 entries`() = runTest {
        val categories = api.getCategories()
        assertThat(categories).hasSize(41)
    }

    @Test
    fun `categories contains работа`() = runTest {
        val categories = api.getCategories()
        assertThat(categories).containsKey("работа")
    }

    @Test
    fun `categories contains айти`() = runTest {
        val categories = api.getCategories()
        assertThat(categories).containsKey("айти")
    }

    @Test
    fun `categories contains котики`() = runTest {
        val categories = api.getCategories()
        assertThat(categories).containsKey("котики")
    }

    @Test
    fun `categories all values are positive`() = runTest {
        val categories = api.getCategories()
        categories.values.forEach { count ->
            assertThat(count).isGreaterThan(0)
        }
    }

    // ============================================================
    // 3. Random joke
    // ============================================================
    @Test
    fun `random joke has text`() = runTest {
        val joke = api.getRandomJoke()
        assertThat(joke.text).isNotEmpty()
    }

    @Test
    fun `random joke has category`() = runTest {
        val joke = api.getRandomJoke()
        assertThat(joke.category).isNotEmpty()
    }

    @Test
    fun `random joke has id`() = runTest {
        val joke = api.getRandomJoke()
        assertThat(joke.id).isGreaterThan(0)
    }

    @Test
    fun `random joke has rating`() = runTest {
        val joke = api.getRandomJoke()
        assertThat(joke.rating).isGreaterThan(0.0)
    }

    // ============================================================
    // 4. Random joke by category=айти
    // ============================================================
    @Test
    fun `random joke by category айти returns category match`() = runTest {
        val response = api.getJokes(category = "айти", count = 1)
        assertThat(response.jokes).isNotEmpty()
        assertThat(response.jokes.first().category).isEqualTo("айти")
    }

    // ============================================================
    // 5. Search q=программист
    // ============================================================
    @Test
    fun `search программист returns total greater than zero`() = runTest {
        // Override for this specific test
        server.enqueue(MockResponse()
            .setBody("""{"jokes":[{"id":100,"text":"Программист — машина","category":"айти","rating":4.3,"tags":[],"semantic_score":0.85}],"total":1}""")
            .setHeader("Content-Type", "application/json"))
        val result = api.searchJokes("программист")
        assertThat(result.total).isGreaterThan(0)
    }

    @Test
    fun `search программист returns non-empty jokes`() = runTest {
        server.enqueue(MockResponse()
            .setBody("""{"jokes":[{"id":100,"text":"Программист — машина","category":"айти","rating":4.3,"tags":[],"semantic_score":0.85}],"total":1}""")
            .setHeader("Content-Type", "application/json"))
        val result = api.searchJokes("программист")
        assertThat(result.jokes).isNotEmpty()
    }

    // ============================================================
    // 6. Search with limit=3
    // ============================================================
    @Test
    fun `search with limit 3 returns exactly 3 jokes`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.SEARCH_LIMIT_3_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.searchJokes("тест", limit = 3)
        assertThat(result.jokes).hasSize(3)
    }

    // ============================================================
    // 7. Context {text: "работа"}
    // ============================================================
    @Test
    fun `context with text работа returns matched_categories containing работа`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.CONTEXT_RABOTA_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.contextJoke(ContextRequest("работа"))
        assertThat(result.matchedCategories).contains("работа")
    }

    // ============================================================
    // 8. Context {text: "айти"}
    // ============================================================
    @Test
    fun `context with text айти returns matched_categories containing айти`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.CONTEXT_AITI_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.contextJoke(ContextRequest("айти"))
        assertThat(result.matchedCategories).contains("айти")
    }

    // ============================================================
    // 9. Context {text: "котики"}
    // ============================================================
    @Test
    fun `context with text котики returns matched_categories containing котики`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.CONTEXT_KOTIKI_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.contextJoke(ContextRequest("котики"))
        assertThat(result.matchedCategories).contains("котики")
    }

    // ============================================================
    // 10. Favorites POST + GET + DELETE cycle
    // ============================================================
    @Test
    fun `favorites POST adds joke`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.FAVORITES_ADD_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.addFavorite(FavoriteRequest(42, "default"))
        assertThat(result.favorites).contains(42)
    }

    @Test
    fun `favorites GET returns jokes`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.FAVORITES_GET_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getFavorites("default")
        assertThat(result.jokes).isNotEmpty()
    }

    @Test
    fun `favorites DELETE removes joke`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.FAVORITES_REMOVE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.removeFavorite(100, "default")
        assertThat(result.favorites).doesNotContain(100)
    }

    // ============================================================
    // 11. Rate joke_id=1 returns new_rating > 0
    // ============================================================
    @Test
    fun `rate joke_id 1 returns new_rating greater than zero`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.RATE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.rateJoke(RatingRequest(1, 5.0))
        assertThat(result.newRating).isGreaterThan(0.0)
    }

    // ============================================================
    // 12. Rate joke_id=999999 returns 404
    // ============================================================
    @Test
    fun `rate joke_id 999999 returns 404`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.RATE_404_JSON)
            .setHeader("Content-Type", "application/json")
            .setResponseCode(404))
        try {
            api.rateJoke(RatingRequest(999999, 5.0))
            assertThat(false).isTrue() // Should not reach
        } catch (e: HttpException) {
            assertThat(e.code()).isEqualTo(404)
        }
    }

    // ============================================================
    // 13. Like joke 1 returns liked=true
    // ============================================================
    @Test
    fun `like joke 1 returns liked true`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.LIKE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.likeJoke(1)
        assertThat(result.liked).isTrue()
    }

    // ============================================================
    // 14. User jokes POST + GET + DELETE
    // ============================================================
    @Test
    fun `user jokes POST creates joke`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.USER_JOKE_CREATE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.createUserJoke(UserJokeRequest("айти", "Мой анекдот про программистов. Достаточно длинный текст.", listOf("программист")))
        assertThat(result.id).isGreaterThan(0)
        assertThat(result.status).isEqualTo("pending_approval")
    }

    @Test
    fun `user jokes GET returns list`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.USER_JOKES_LIST_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getUserJokes(0)
        assertThat(result.jokes).isNotEmpty()
    }

    @Test
    fun `user jokes DELETE returns deleted true`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.USER_JOKE_DELETE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.deleteUserJoke(5001)
        assertThat(result.deleted).isTrue()
    }

    // ============================================================
    // 15. EN jokes total > 0
    // ============================================================
    @Test
    fun `EN jokes returns total greater than zero`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.EN_JOKES_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getEnglishJokes(5)
        assertThat(result.total).isGreaterThan(0)
    }

    @Test
    fun `EN jokes returns jokes list`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.EN_JOKES_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getEnglishJokes(5)
        assertThat(result.jokes).isNotEmpty()
    }

    // ============================================================
    // 16. Social top jokes not empty
    // ============================================================
    @Test
    fun `social top returns non-empty jokes`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.SOCIAL_TOP_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getSocialTop("day", 10)
        assertThat(result.jokes).isNotEmpty()
    }

    @Test
    fun `social top returns correct period`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.SOCIAL_TOP_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getSocialTop("day", 10)
        assertThat(result.period).isEqualTo("day")
    }

    // ============================================================
    // 17. TTS returns audio_file
    // ============================================================
    @Test
    fun `TTS returns audio_file present`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.TTS_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.textToSpeech(TtsRequest("Текст анекдота для озвучки"))
        assertThat(result.audioFile).isNotEmpty()
        assertThat(result.audioFile).contains("/data/tts/")
    }

    @Test
    fun `TTS returns text`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.TTS_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.textToSpeech(TtsRequest("Текст анекдота для озвучки"))
        assertThat(result.text).isNotEmpty()
    }

    // ============================================================
    // 18. Generate returns joke with generated=true
    // ============================================================
    @Test
    fun `generate returns joke with generated true`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.GENERATE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.generateJoke(GenerateRequest("программист"))
        assertThat(result.joke.generated).isTrue()
    }

    @Test
    fun `generate returns joke with text`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.GENERATE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.generateJoke(GenerateRequest("программист"))
        assertThat(result.joke.text).isNotEmpty()
    }

    @Test
    fun `generate returns joke with generator field`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.GENERATE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.generateJoke(GenerateRequest("программист"))
        assertThat(result.joke.generator).isNotNull()
        assertThat(result.joke.generator).isEqualTo("llm")
    }

    // ============================================================
    // 19. Personalize POST + GET
    // ============================================================
    @Test
    fun `personalize POST returns updated`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.PERSONALIZE_POST_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.updatePreferences("user123", "айти", "политика")
        assertThat(result.status).isEqualTo("updated")
    }

    @Test
    fun `personalize GET returns jokes`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.PERSONALIZE_GET_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getPersonalized("user123", 3)
        assertThat(result.jokes).isNotEmpty()
    }

    // ============================================================
    // 20. Analytics stats + popular
    // ============================================================
    @Test
    fun `analytics stats returns total_events`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.ANALYTICS_STATS_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getAnalyticsStats()
        assertThat(result.totalEvents).isGreaterThan(0)
    }

    @Test
    fun `analytics stats returns unique_users`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.ANALYTICS_STATS_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getAnalyticsStats()
        assertThat(result.uniqueUsers).isGreaterThan(0)
    }

    @Test
    fun `analytics stats returns top_categories`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.ANALYTICS_STATS_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getAnalyticsStats()
        assertThat(result.topCategories).isNotEmpty()
    }

    @Test
    fun `analytics popular returns results`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.ANALYTICS_POPULAR_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getPopularTopics(7)
        assertThat(result.popular).isNotEmpty()
        assertThat(result.periodDays).isEqualTo(7)
    }

    // ============================================================
    // 21. Monetization ad + premium
    // ============================================================
    @Test
    fun `monetization ad returns ad with show=true`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.AD_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getAd()
        assertThat(result.ad.show).isTrue()
        assertThat(result.ad.type).isEqualTo("banner")
    }

    @Test
    fun `monetization premium returns is_premium false`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.PREMIUM_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.getPremiumStatus("user123")
        assertThat(result.isPremium).isFalse()
        assertThat(result.features).contains("no_ads")
        assertThat(result.price).contains("199")
    }

    // ============================================================
    // 22. Empty text → 400
    // ============================================================
    @Test
    fun `context with empty text returns 400`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.ERROR_400_JSON)
            .setHeader("Content-Type", "application/json")
            .setResponseCode(400))
        try {
            api.contextJoke(ContextRequest(""))
            assertThat(false).isTrue() // Should not reach here
        } catch (e: HttpException) {
            assertThat(e.code()).isEqualTo(400)
        }
    }

    // ============================================================
    // 23. Gibberish → 0 results
    // ============================================================
    @Test
    fun `search gibberish returns 0 results`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.SEARCH_EMPTY_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.searchJokes("xyznonexistentgibberish")
        assertThat(result.total).isEqualTo(0)
        assertThat(result.jokes).isEmpty()
    }

    // ============================================================
    // Additional edge case tests
    // ============================================================
    @Test
    fun `stats request hits correct endpoint`() = runTest {
        api.getStats()
        val request = server.takeRequest()
        assertThat(request.path).isEqualTo("/api/stats")
    }

    @Test
    fun `categories request hits correct endpoint`() = runTest {
        api.getCategories()
        val request = server.takeRequest()
        assertThat(request.path).isEqualTo("/api/categories")
    }

    @Test
    fun `random joke request hits correct endpoint`() = runTest {
        api.getRandomJoke()
        val request = server.takeRequest()
        assertThat(request.path).isEqualTo("/api/joke/random")
    }

    @Test
    fun `like request uses POST method`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.LIKE_JSON)
            .setHeader("Content-Type", "application/json"))
        api.likeJoke(1)
        val request = server.takeRequest()
        assertThat(request.method).isEqualTo("POST")
    }

    @Test
    fun `rate request uses POST method`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.RATE_JSON)
            .setHeader("Content-Type", "application/json"))
        api.rateJoke(RatingRequest(1, 5.0))
        val request = server.takeRequest()
        assertThat(request.method).isEqualTo("POST")
    }

    @Test
    fun `favorite add uses POST method`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.FAVORITES_ADD_JSON)
            .setHeader("Content-Type", "application/json"))
        api.addFavorite(FavoriteRequest(42))
        val request = server.takeRequest()
        assertThat(request.method).isEqualTo("POST")
    }

    @Test
    fun `favorite delete uses DELETE method`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.FAVORITES_REMOVE_JSON)
            .setHeader("Content-Type", "application/json"))
        api.removeFavorite(42)
        val request = server.takeRequest()
        assertThat(request.method).isEqualTo("DELETE")
    }

    @Test
    fun `context response has search_method field`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.CONTEXT_RABOTA_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.contextJoke(ContextRequest("работа"))
        assertThat(result.searchMethod).isEqualTo("semantic")
    }

    @Test
    fun `generate response has matched_categories`() = runTest {
        server.enqueue(MockResponse()
            .setBody(MockServer.GENERATE_JSON)
            .setHeader("Content-Type", "application/json"))
        val result = api.generateJoke(GenerateRequest("айти"))
        assertThat(result.matchedCategories).isNotEmpty()
    }
}
