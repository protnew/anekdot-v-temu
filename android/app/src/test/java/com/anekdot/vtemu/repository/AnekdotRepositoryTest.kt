package com.anekdot.vtemu.repository

import com.anekdot.vtemu.api.AnekdotApi
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.*
import com.anekdot.vtemu.util.MockServer
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.*
import retrofit2.HttpException

class AnekdotRepositoryTest {

    private lateinit var mockApi: AnekdotApi
    private lateinit var repository: AnekdotRepository

    @Before
    fun setUp() {
        mockApi = mock(AnekdotApi::class.java)
        repository = AnekdotRepository(mockApi, maxRetries = 2, retryDelayMs = 10)
    }

    // ============================================================
    // Stats
    // ============================================================
    @Test
    fun `getStats returns success with correct data`() = runTest {
        val expected = StatsResponse(
            totalJokes = 112360, enJokes = 15, categories = 41,
            favoritesCount = 256, historyCount = 1543, avgRating = 4.2,
            vocabularySize = 8450, version = "3.5.0"
        )
        `when`(mockApi.getStats()).thenReturn(expected)

        val result = repository.getStats()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.totalJokes).isEqualTo(112360)
        assertThat(result.data.version).isEqualTo("3.5.0")
    }

    @Test
    fun `getStats returns error on exception`() = runTest {
        `when`(mockApi.getStats()).thenThrow(RuntimeException("Network error"))

        val result = repository.getStats()
        assertThat(result.isError).isTrue()
        assertThat((result as ApiResponse.Error).message).isEqualTo("Network error")
    }

    // ============================================================
    // Categories
    // ============================================================
    @Test
    fun `getCategories returns success with category list`() = runTest {
        val expected = mapOf("работа" to 5200, "айти" to 3800)
        `when`(mockApi.getCategories()).thenReturn(expected)

        val result = repository.getCategories()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data).hasSize(2)
        assertThat(result.data).contains("работа")
    }

    // ============================================================
    // Random joke
    // ============================================================
    @Test
    fun `getRandomJoke returns success`() = runTest {
        val expected = Joke(id = 42, text = "Текст анекдота", category = "айти", rating = 4.7)
        `when`(mockApi.getRandomJoke()).thenReturn(expected)

        val result = repository.getRandomJoke()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.id).isEqualTo(42)
        assertThat(result.data.text).isEqualTo("Текст анекдота")
    }

    @Test
    fun `getRandomJoke retries on server error and succeeds`() = runTest {
        val joke = Joke(id = 42, text = "Текст", category = "айти", rating = 4.7)
        `when`(mockApi.getRandomJoke())
            .thenThrow(RuntimeException("Server error"))
            .thenReturn(joke)

        val result = repository.getRandomJoke()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.id).isEqualTo(42)
    }

    @Test
    fun `getRandomJoke does not retry on client error`() = runTest {
        val httpException = mock(HttpException::class.java)
        `when`(httpException.code()).thenReturn(400)
        `when`(httpException.message()).thenReturn("Bad Request")
        `when`(mockApi.getRandomJoke()).thenThrow(httpException)

        val result = repository.getRandomJoke()
        assertThat(result.isError).isTrue()
        verify(mockApi, times(1)).getRandomJoke()
    }

    @Test
    fun `getRandomJoke returns error after max retries`() = runTest {
        `when`(mockApi.getRandomJoke()).thenThrow(RuntimeException("Persistent error"))

        val result = repository.getRandomJoke()
        assertThat(result.isError).isTrue()
        verify(mockApi, times(2)).getRandomJoke() // maxRetries = 2
    }

    // ============================================================
    // Search
    // ============================================================
    @Test
    fun `searchJokes returns success`() = runTest {
        val expected = JokesResponse(
            jokes = listOf(Joke(id = 100, text = "Шутка", category = "айти", rating = 4.3)),
            total = 1
        )
        `when`(mockApi.searchJokes("тест", 10)).thenReturn(expected)

        val result = repository.searchJokes("тест", 10)
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.total).isEqualTo(1)
        assertThat(result.data.jokes).hasSize(1)
    }

    // ============================================================
    // Context search
    // ============================================================
    @Test
    fun `contextSearch returns success with matched categories`() = runTest {
        val expected = ContextResponse(
            jokes = listOf(Joke(id = 300, text = "Анекдот про работу", category = "работа", rating = 4.4)),
            matchedCategories = listOf("работа"),
            context = "работа",
            searchMethod = "semantic"
        )
        `when`(mockApi.contextJoke(any())).thenReturn(expected)

        val result = repository.contextSearch("работа")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.matchedCategories).contains("работа")
    }

    // ============================================================
    // Favorites
    // ============================================================
    @Test
    fun `addFavorite returns success`() = runTest {
        val expected = FavoriteIdsResponse(favorites = listOf(1, 42))
        `when`(mockApi.addFavorite(any())).thenReturn(expected)

        val result = repository.addFavorite("42", "default")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.favorites).contains(42)
    }

    @Test
    fun `getFavorites returns success`() = runTest {
        val expected = FavoritesResponse(
            jokes = listOf(Joke(id = 42, text = "Избранный", category = "айти", rating = 4.7))
        )
        `when`(mockApi.getFavorites("default")).thenReturn(expected)

        val result = repository.getFavorites("default")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.jokes).hasSize(1)
    }

    @Test
    fun `removeFavorite returns success`() = runTest {
        val expected = FavoriteIdsResponse(favorites = listOf(42))
        `when`(mockApi.removeFavorite(100, "default")).thenReturn(expected)

        val result = repository.removeFavorite("100", "default")
        assertThat(result.isSuccess).isTrue()
    }

    // ============================================================
    // Rate
    // ============================================================
    @Test
    fun `rateJoke returns success with new rating`() = runTest {
        val expected = RatingResponse(newRating = 4.4)
        `when`(mockApi.rateJoke(any())).thenReturn(expected)

        val result = repository.rateJoke(1, 5)
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.newRating).isGreaterThan(0.0)
    }

    @Test
    fun `rateJoke returns error on 404`() = runTest {
        val httpException = mock(HttpException::class.java)
        `when`(httpException.code()).thenReturn(404)
        `when`(httpException.message()).thenReturn("Not Found")
        `when`(mockApi.rateJoke(any())).thenThrow(httpException)

        val result = repository.rateJoke(999999, 5)
        assertThat(result.isError).isTrue()
    }

    // ============================================================
    // Like
    // ============================================================
    @Test
    fun `likeJoke returns success`() = runTest {
        val expected = LikeResponse(liked = true)
        `when`(mockApi.likeJoke(1)).thenReturn(expected)

        val result = repository.likeJoke(1)
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.liked).isTrue()
    }

    // ============================================================
    // User jokes
    // ============================================================
    @Test
    fun `createUserJoke returns success`() = runTest {
        val expected = UserJokeResponse(id = 5001, status = "pending_approval")
        `when`(mockApi.createUserJoke(any())).thenReturn(expected)

        val result = repository.createUserJoke("айти", "Длинный текст анекдота про программистов.")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.id).isEqualTo(5001)
    }

    @Test
    fun `getUserJokes returns success`() = runTest {
        val expected = UserJokesResponse(
            jokes = listOf(
                UserJoke(id = 5001, userId = "anonymous", category = "айти",
                    text = "Анекдот", tags = listOf("программист"))
            )
        )
        `when`(mockApi.getUserJokes(0)).thenReturn(expected)

        val result = repository.getUserJokes(0)
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.jokes).hasSize(1)
    }

    @Test
    fun `deleteUserJoke returns success`() = runTest {
        val expected = DeleteResponse(deleted = true)
        `when`(mockApi.deleteUserJoke(5001)).thenReturn(expected)

        val result = repository.deleteUserJoke(5001)
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.deleted).isTrue()
    }

    // ============================================================
    // English jokes
    // ============================================================
    @Test
    fun `getEnglishJokes returns success`() = runTest {
        val expected = JokesResponse(
            jokes = listOf(
                Joke(id = 8001, text = "Why do programmers prefer dark mode?", category = "en_it", rating = 4.6)
            ),
            total = 15
        )
        `when`(mockApi.getEnglishJokes(5)).thenReturn(expected)

        val result = repository.getEnglishJokes(5)
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.total).isGreaterThan(0)
    }

    // ============================================================
    // Social top
    // ============================================================
    @Test
    fun `getSocialTop returns success`() = runTest {
        val expected = SocialTopResponse(
            jokes = listOf(Joke(id = 42, text = "Топ анекдот", category = "айти", rating = 4.9)),
            period = "day"
        )
        `when`(mockApi.getSocialTop("day", 10)).thenReturn(expected)

        val result = repository.getSocialTop()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.jokes).isNotEmpty()
    }

    // ============================================================
    // TTS
    // ============================================================
    @Test
    fun `textToSpeech returns success`() = runTest {
        val expected = TtsResponse(
            text = "Текст", audioFile = "/data/tts/test.mp3",
            durationEstimate = "2 сек", generator = "gTTS"
        )
        `when`(mockApi.textToSpeech(any())).thenReturn(expected)

        val result = repository.textToSpeech("Текст")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.audioFile).isNotEmpty()
    }

    // ============================================================
    // Generate
    // ============================================================
    @Test
    fun `generateJoke returns success`() = runTest {
        val expected = GenerateResponse(
            joke = Joke(id = 99999, text = "Сгенерировано", category = "айти", rating = 4.5, generated = true),
            matchedCategories = listOf("айти")
        )
        `when`(mockApi.generateJoke(any())).thenReturn(expected)

        val result = repository.generateJoke("айти")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.joke.generated).isTrue()
    }

    // ============================================================
    // Personalize
    // ============================================================
    @Test
    fun `updatePreferences returns success`() = runTest {
        val expected = PersonalizeResponse(status = "updated")
        `when`(mockApi.updatePreferences("user1", "айти", "")).thenReturn(expected)

        val result = repository.updatePreferences("user1", "айти", "")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.status).isEqualTo("updated")
    }

    @Test
    fun `getPersonalized returns success`() = runTest {
        val expected = PersonalizedJokesResponse(
            jokes = listOf(Joke(id = 42, text = "Анекдот", category = "айти", rating = 4.7))
        )
        `when`(mockApi.getPersonalized("user1", 3)).thenReturn(expected)

        val result = repository.getPersonalized("user1")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.jokes).isNotEmpty()
    }

    // ============================================================
    // Analytics
    // ============================================================
    @Test
    fun `getAnalyticsStats returns success`() = runTest {
        val expected = AnalyticsStatsResponse(
            totalEvents = 5420, uniqueUsers = 328,
            topCategories = listOf(CategoryCount(category = "айти", count = 1200))
        )
        `when`(mockApi.getAnalyticsStats()).thenReturn(expected)

        val result = repository.getAnalyticsStats()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.totalEvents).isEqualTo(5420)
    }

    @Test
    fun `getPopularTopics returns success`() = runTest {
        val expected = PopularResponse(
            popular = listOf(CategoryCount(category = "айти", count = 45)),
            periodDays = 7
        )
        `when`(mockApi.getPopularTopics(7)).thenReturn(expected)

        val result = repository.getPopularTopics()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.popular).isNotEmpty()
    }

    // ============================================================
    // Monetization
    // ============================================================
    @Test
    fun `getAd returns success`() = runTest {
        val expected = AdResponse(
            ad = AdInfo(type = "banner", text = "Premium!", link = "#premium", show = true)
        )
        `when`(mockApi.getAd()).thenReturn(expected)

        val result = repository.getAd()
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.ad.show).isTrue()
    }

    @Test
    fun `getPremiumStatus returns success`() = runTest {
        val expected = PremiumResponse(
            isPremium = false, features = listOf("no_ads"), price = "199₽/мес"
        )
        `when`(mockApi.getPremiumStatus("user1")).thenReturn(expected)

        val result = repository.getPremiumStatus("user1")
        assertThat(result.isSuccess).isTrue()
        assertThat((result as ApiResponse.Success).data.isPremium).isFalse()
    }

    // ============================================================
    // Error handling mapping
    // ============================================================
    @Test
    fun `repository maps HttpException to ApiResponse Error`() = runTest {
        val httpException = mock(HttpException::class.java)
        `when`(httpException.code()).thenReturn(500)
        `when`(httpException.message()).thenReturn("Internal Server Error")
        `when`(mockApi.getStats()).thenThrow(httpException)

        val result = repository.getStats()
        assertThat(result.isError).isTrue()
        assertThat((result as ApiResponse.Error).code).isEqualTo(500)
    }

    @Test
    fun `repository maps IOException to ApiResponse Error`() = runTest {
        `when`(mockApi.getStats()).thenThrow(java.io.IOException("Connection refused"))

        val result = repository.getStats()
        assertThat(result.isError).isTrue()
        assertThat((result as ApiResponse.Error).message).isEqualTo("Connection refused")
    }

    // ============================================================
    // Retry logic
    // ============================================================
    @Test
    fun `getRandomJoke retries on failure and succeeds`() = runTest {
        `when`(mockApi.getRandomJoke())
            .thenThrow(RuntimeException("Timeout"))
            .thenReturn(Joke(id = 1, text = "Т", category = "айти", rating = 4.0))

        val result = repository.getRandomJoke()
        assertThat(result.isSuccess).isTrue()
        verify(mockApi, times(2)).getRandomJoke()
    }

    @Test
    fun `searchJokes retries and returns error after exhausting retries`() = runTest {
        `when`(mockApi.searchJokes("тест", 10))
            .thenThrow(RuntimeException("Error 1"))
            .thenThrow(RuntimeException("Error 2"))

        val result = repository.searchJokes("тест", 10)
        assertThat(result.isError).isTrue()
        verify(mockApi, times(2)).searchJokes("тест", 10)
    }
}
