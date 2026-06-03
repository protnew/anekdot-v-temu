package com.anekdot.vtemu.model

import com.google.common.truth.Truth.assertThat
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import org.junit.Before
import org.junit.Test

class ModelTest {

    private lateinit var moshi: Moshi

    @Before
    fun setUp() {
        moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()
    }

    // ============================================================
    // Joke data class
    // ============================================================
    @Test
    fun `Joke creation with all fields`() {
        val joke = Joke(
            id = 42,
            text = "Программист ставит на тумбочку два стакана.",
            category = "айти",
            rating = 4.7,
            tags = listOf("программист", "сон"),
            likes = 128,
            views = 1540,
            generated = false,
            generator = null,
            semanticScore = null
        )
        assertThat(joke.id).isEqualTo(42)
        assertThat(joke.text).isEqualTo("Программист ставит на тумбочку два стакана.")
        assertThat(joke.category).isEqualTo("айти")
        assertThat(joke.rating).isEqualTo(4.7)
        assertThat(joke.tags).containsExactly("программист", "сон")
        assertThat(joke.likes).isEqualTo(128)
        assertThat(joke.views).isEqualTo(1540)
        assertThat(joke.generated).isFalse()
        assertThat(joke.generator).isNull()
        assertThat(joke.semanticScore).isNull()
    }

    @Test
    fun `Joke creation with defaults`() {
        val joke = Joke(id = 1, text = "Текст", category = "разное")
        assertThat(joke.rating).isEqualTo(4.0)
        assertThat(joke.tags).isEmpty()
        assertThat(joke.likes).isEqualTo(0)
        assertThat(joke.views).isEqualTo(0)
        assertThat(joke.generated).isFalse()
        assertThat(joke.generator).isNull()
        assertThat(joke.semanticScore).isNull()
    }

    @Test
    fun `Joke serialization and deserialization with Moshi`() {
        val adapter = moshi.adapter(Joke::class.java)
        val joke = Joke(
            id = 42,
            text = "Текст анекдота",
            category = "айти",
            rating = 4.7,
            tags = listOf("программист"),
            likes = 100,
            views = 500
        )

        val json = adapter.toJson(joke)
        assertThat(json).contains("\"id\":42")
        assertThat(json).contains("\"text\":\"Текст анекдота\"")
        assertThat(json).contains("\"category\":\"айти\"")
        assertThat(json).contains("\"rating\":4.7")

        val deserialized = adapter.fromJson(json)!!
        assertThat(deserialized.id).isEqualTo(42)
        assertThat(deserialized.text).isEqualTo("Текст анекдота")
        assertThat(deserialized.category).isEqualTo("айти")
        assertThat(deserialized.rating).isEqualTo(4.7)
        assertThat(deserialized.tags).containsExactly("программист")
        assertThat(deserialized.likes).isEqualTo(100)
    }

    @Test
    fun `Joke with generated=true serializes correctly`() {
        val adapter = moshi.adapter(Joke::class.java)
        val joke = Joke(
            id = 99999,
            text = "Сгенерированный анекдот",
            category = "айти",
            rating = 4.5,
            generated = true,
            generator = "llm"
        )

        val json = adapter.toJson(joke)
        assertThat(json).contains("\"generated\":true")
        assertThat(json).contains("\"generator\":\"llm\"")

        val deserialized = adapter.fromJson(json)!!
        assertThat(deserialized.generated).isTrue()
        assertThat(deserialized.generator).isEqualTo("llm")
    }

    @Test
    fun `Joke with semantic_score deserializes`() {
        val adapter = moshi.adapter(Joke::class.java)
        val json = """{"id":100,"text":"Текст","category":"айти","rating":4.3,"tags":["тест"],"semantic_score":0.85}"""

        val joke = adapter.fromJson(json)!!
        assertThat(joke.semanticScore).isEqualTo(0.85)
    }

    @Test
    fun `Joke with empty tags serializes`() {
        val adapter = moshi.adapter(Joke::class.java)
        val joke = Joke(id = 1, text = "Т", category = "разное", tags = emptyList())
        val json = adapter.toJson(joke)
        assertThat(json).contains("\"tags\":[]")
    }

    // ============================================================
    // StatsResponse
    // ============================================================
    @Test
    fun `StatsResponse creation and serialization`() {
        val adapter = moshi.adapter(StatsResponse::class.java)
        val stats = StatsResponse(
            totalJokes = 112360,
            enJokes = 15,
            categories = 41,
            favoritesCount = 256,
            historyCount = 1543,
            avgRating = 4.2,
            vocabularySize = 8450,
            version = "3.5.0"
        )

        val json = adapter.toJson(stats)
        assertThat(json).contains("\"total_jokes\":112360")
        assertThat(json).contains("\"categories\":41")
        assertThat(json).contains("\"version\":\"3.5.0\"")

        val deserialized = adapter.fromJson(json)!!
        assertThat(deserialized.totalJokes).isEqualTo(112360)
        assertThat(deserialized.categories).isEqualTo(41)
        assertThat(deserialized.version).isEqualTo("3.5.0")
    }

    @Test
    fun `StatsResponse deserialization from API JSON`() {
        val adapter = moshi.adapter(StatsResponse::class.java)
        val json = """{"total_jokes":112360,"en_jokes":15,"categories":41,"favorites_count":256,"history_count":1543,"avg_rating":4.2,"vocabulary_size":8450,"version":"3.5.0"}"""

        val stats = adapter.fromJson(json)!!
        assertThat(stats.totalJokes).isEqualTo(112360)
        assertThat(stats.enJokes).isEqualTo(15)
        assertThat(stats.categories).isEqualTo(41)
        assertThat(stats.avgRating).isWithin(0.01).of(4.2)
    }

    // ============================================================
    // ContextRequest / ContextResponse
    // ============================================================
    @Test
    fun `ContextRequest serialization`() {
        val adapter = moshi.adapter(ContextRequest::class.java)
        val request = ContextRequest(text = "работа", count = 5, category = null)

        val json = adapter.toJson(request)
        assertThat(json).contains("\"text\":\"работа\"")
        assertThat(json).contains("\"count\":5")
    }

    @Test
    fun `ContextResponse deserialization`() {
        val adapter = moshi.adapter(ContextResponse::class.java)
        val json = """{"jokes":[{"id":300,"text":"Анекдот","category":"работа","rating":4.4,"tags":[]}],"matched_categories":["работа"],"context":"работа","search_method":"semantic"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.jokes).hasSize(1)
        assertThat(response.matchedCategories).containsExactly("работа")
        assertThat(response.context).isEqualTo("работа")
        assertThat(response.searchMethod).isEqualTo("semantic")
    }

    // ============================================================
    // GenerateResponse
    // ============================================================
    @Test
    fun `GenerateResponse deserialization with generated joke`() {
        val adapter = moshi.adapter(GenerateResponse::class.java)
        val json = """{"joke":{"id":99999,"text":"Сгенерировано","category":"айти","rating":4.5,"tags":[],"generated":true,"generator":"llm"},"matched_categories":["айти"]}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.joke.generated).isTrue()
        assertThat(response.joke.generator).isEqualTo("llm")
        assertThat(response.matchedCategories).contains("айти")
    }

    // ============================================================
    // FavoriteRequest / FavoriteIdsResponse
    // ============================================================
    @Test
    fun `FavoriteRequest serialization`() {
        val adapter = moshi.adapter(FavoriteRequest::class.java)
        val request = FavoriteRequest(jokeId = 42, userId = "default")

        val json = adapter.toJson(request)
        assertThat(json).contains("\"joke_id\":42")
        assertThat(json).contains("\"user_id\":\"default\"")
    }

    @Test
    fun `FavoriteIdsResponse deserialization`() {
        val adapter = moshi.adapter(FavoriteIdsResponse::class.java)
        val json = """{"favorites":[1,42,100]}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.favorites).containsExactly(1, 42, 100)
    }

    // ============================================================
    // RatingRequest / RatingResponse
    // ============================================================
    @Test
    fun `RatingRequest serialization`() {
        val adapter = moshi.adapter(RatingRequest::class.java)
        val request = RatingRequest(jokeId = 1, rating = 5.0)

        val json = adapter.toJson(request)
        assertThat(json).contains("\"joke_id\":1")
        assertThat(json).contains("\"rating\":5.0")
    }

    @Test
    fun `RatingResponse deserialization`() {
        val adapter = moshi.adapter(RatingResponse::class.java)
        val json = """{"new_rating":4.4}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.newRating).isWithin(0.01).of(4.4)
    }

    // ============================================================
    // LikeResponse
    // ============================================================
    @Test
    fun `LikeResponse deserialization`() {
        val adapter = moshi.adapter(LikeResponse::class.java)
        val json = """{"liked":true}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.liked).isTrue()
    }

    // ============================================================
    // UserJokeRequest / UserJokeResponse / UserJoke
    // ============================================================
    @Test
    fun `UserJokeRequest serialization`() {
        val adapter = moshi.adapter(UserJokeRequest::class.java)
        val request = UserJokeRequest(
            category = "айти",
            text = "Мой анекдот.",
            tags = listOf("программист")
        )

        val json = adapter.toJson(request)
        assertThat(json).contains("\"category\":\"айти\"")
        assertThat(json).contains("\"text\":\"Мой анекдот.\"")
    }

    @Test
    fun `UserJokeResponse deserialization`() {
        val adapter = moshi.adapter(UserJokeResponse::class.java)
        val json = """{"id":5001,"status":"pending_approval"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.id).isEqualTo(5001)
        assertThat(response.status).isEqualTo("pending_approval")
    }

    @Test
    fun `UserJoke deserialization`() {
        val adapter = moshi.adapter(UserJoke::class.java)
        val json = """{"id":5001,"user_id":"anonymous","category":"айти","text":"Текст","rating":4.0,"tags":["тест"],"approved":0}"""

        val joke = adapter.fromJson(json)!!
        assertThat(joke.id).isEqualTo(5001)
        assertThat(joke.userId).isEqualTo("anonymous")
        assertThat(joke.category).isEqualTo("айти")
        assertThat(joke.approved).isEqualTo(0)
    }

    // ============================================================
    // DeleteResponse
    // ============================================================
    @Test
    fun `DeleteResponse deserialization`() {
        val adapter = moshi.adapter(DeleteResponse::class.java)
        val json = """{"deleted":true}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.deleted).isTrue()
    }

    // ============================================================
    // SocialTopResponse
    // ============================================================
    @Test
    fun `SocialTopResponse deserialization`() {
        val adapter = moshi.adapter(SocialTopResponse::class.java)
        val json = """{"jokes":[{"id":42,"text":"Топ","category":"айти","rating":4.9}],"period":"day"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.jokes).hasSize(1)
        assertThat(response.period).isEqualTo("day")
    }

    // ============================================================
    // TtsResponse
    // ============================================================
    @Test
    fun `TtsResponse deserialization`() {
        val adapter = moshi.adapter(TtsResponse::class.java)
        val json = """{"text":"Текст","audio_file":"/data/tts/test.mp3","duration_estimate":"2 сек","generator":"gTTS"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.audioFile).isEqualTo("/data/tts/test.mp3")
        assertThat(response.generator).isEqualTo("gTTS")
    }

    // ============================================================
    // AnalyticsStatsResponse
    // ============================================================
    @Test
    fun `AnalyticsStatsResponse deserialization`() {
        val adapter = moshi.adapter(AnalyticsStatsResponse::class.java)
        val json = """{"total_events":5420,"unique_users":328,"top_categories":[{"category":"айти","cnt":1200}]}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.totalEvents).isEqualTo(5420)
        assertThat(response.uniqueUsers).isEqualTo(328)
        assertThat(response.topCategories).hasSize(1)
        assertThat(response.topCategories.first().category).isEqualTo("айти")
        assertThat(response.topCategories.first().count).isEqualTo(1200)
    }

    // ============================================================
    // PopularResponse
    // ============================================================
    @Test
    fun `PopularResponse deserialization`() {
        val adapter = moshi.adapter(PopularResponse::class.java)
        val json = """{"popular":[{"category":"айти","cnt":45}],"period_days":7}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.popular).hasSize(1)
        assertThat(response.periodDays).isEqualTo(7)
    }

    // ============================================================
    // AdResponse / AdInfo
    // ============================================================
    @Test
    fun `AdResponse deserialization`() {
        val adapter = moshi.adapter(AdResponse::class.java)
        val json = """{"ad":{"type":"banner","text":"Premium!","link":"#premium","show":true}}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.ad.type).isEqualTo("banner")
        assertThat(response.ad.show).isTrue()
    }

    // ============================================================
    // PremiumResponse
    // ============================================================
    @Test
    fun `PremiumResponse deserialization`() {
        val adapter = moshi.adapter(PremiumResponse::class.java)
        val json = """{"is_premium":false,"features":["no_ads","exclusive"],"price":"199₽/мес"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.isPremium).isFalse()
        assertThat(response.features).contains("no_ads")
        assertThat(response.price).isEqualTo("199₽/мес")
    }

    // ============================================================
    // PersonalizeResponse
    // ============================================================
    @Test
    fun `PersonalizeResponse deserialization`() {
        val adapter = moshi.adapter(PersonalizeResponse::class.java)
        val json = """{"status":"updated"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.status).isEqualTo("updated")
    }

    // ============================================================
    // JokesResponse
    // ============================================================
    @Test
    fun `JokesResponse deserialization with multiple jokes`() {
        val adapter = moshi.adapter(JokesResponse::class.java)
        val json = """{"jokes":[{"id":1,"text":"Шутка 1","category":"айти","rating":4.0},{"id":2,"text":"Шутка 2","category":"работа","rating":4.5}],"total":2}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.jokes).hasSize(2)
        assertThat(response.total).isEqualTo(2)
        assertThat(response.jokes[0].id).isEqualTo(1)
        assertThat(response.jokes[1].category).isEqualTo("работа")
    }

    @Test
    fun `JokesResponse with empty jokes`() {
        val adapter = moshi.adapter(JokesResponse::class.java)
        val json = """{"jokes":[],"total":0}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.jokes).isEmpty()
        assertThat(response.total).isEqualTo(0)
    }

    // ============================================================
    // ErrorResponse
    // ============================================================
    @Test
    fun `ErrorResponse deserialization`() {
        val adapter = moshi.adapter(ErrorResponse::class.java)
        val json = """{"detail":"Joke not found"}"""

        val response = adapter.fromJson(json)!!
        assertThat(response.detail).isEqualTo("Joke not found")
    }

    // ============================================================
    // CategoriesResponse (Map deserialization)
    // ============================================================
    @Test
    fun `Categories map deserialization`() {
        val adapter = moshi.adapter(Map::class.java)
        val json = """{"работа":5200,"айти":3800,"котики":950}"""

        @Suppress("UNCHECKED_CAST")
        val categories = adapter.fromJson(json) as Map<String, Int>
        assertThat(categories).hasSize(3)
        assertThat(categories["работа"]).isEqualTo(5200)
        assertThat(categories["айти"]).isEqualTo(3800)
        assertThat(categories["котики"]).isEqualTo(950)
    }

    // ============================================================
    // Copy and equality tests
    // ============================================================
    @Test
    fun `Joke copy creates new instance with modified fields`() {
        val joke = Joke(id = 1, text = "Оригинал", category = "айти", rating = 4.0)
        val modified = joke.copy(rating = 4.5, text = "Изменён")

        assertThat(modified.id).isEqualTo(1)
        assertThat(modified.text).isEqualTo("Изменён")
        assertThat(modified.rating).isEqualTo(4.5)
        assertThat(modified.category).isEqualTo("айти")
        assertThat(joke.text).isEqualTo("Оригинал") // original unchanged
    }

    @Test
    fun `Joke equality works correctly`() {
        val joke1 = Joke(id = 1, text = "Текст", category = "айти", rating = 4.0)
        val joke2 = Joke(id = 1, text = "Текст", category = "айти", rating = 4.0)
        val joke3 = Joke(id = 2, text = "Текст", category = "айти", rating = 4.0)

        assertThat(joke1).isEqualTo(joke2)
        assertThat(joke1).isNotEqualTo(joke3)
    }
}
