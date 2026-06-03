package com.anekdot.vtemu.util

import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest

/**
 * Helper for setting up MockWebServer with preconfigured JSON responses
 * for every API endpoint in the Anekdot API.
 */
object MockServer {

    //region JSON Responses

    const val STATS_JSON = """{
        "total_jokes": 112360,
        "en_jokes": 15,
        "categories": 41,
        "favorites_count": 256,
        "history_count": 1543,
        "avg_rating": 4.2,
        "vocabulary_size": 8450,
        "version": "3.5.0"
    }"""

    const val CATEGORIES_JSON = """{
        "работа": 5200,
        "айти": 3800,
        "деньги": 2900,
        "семья": 4500,
        "политика": 2100,
        "здоровье": 1800,
        "путешествия": 1500,
        "еда": 2200,
        "наука": 1600,
        "спорт": 1900,
        "образование": 2100,
        "отношения": 3200,
        "коронавирус": 800,
        "искусственный интеллект": 1400,
        "друзья": 2700,
        "котики": 950,
        "авто": 2300,
        "магазины": 1100,
        "дети": 2600,
        "реклама": 900,
        "разное": 8500,
        "студенты": 3200,
        "врачи": 2100,
        "армия": 1800,
        "школа": 2400,
        "москва": 1600,
        "женская логика": 2900,
        "мужская логика": 2700,
        "тёща": 1800,
        "бабушка": 1200,
        "евреи": 2500,
        "английские": 1500,
        "чёрный юмор": 2100,
        "философия": 800,
        "музыка": 1100,
        "кино": 1300,
        "книги": 700,
        "история": 1400,
        "религия": 900,
        "загадки": 600,
        "лицензии": 200
    }"""

    const val RANDOM_JOKE_JSON = """{
        "id": 42,
        "text": "Программист ставит на тумбочку перед сном два стакана: один с водой — если захочет пить, другой пустой — если не захочет.",
        "category": "айти",
        "rating": 4.7,
        "tags": ["программист", "сон"],
        "likes": 128,
        "views": 1540
    }"""

    const val RANDOM_JOKE_AITI_JSON = """{
        "id": 55,
        "text": "Почему программисты путают Хэллоуин и Рождество? Потому что Oct 31 = Dec 25.",
        "category": "айти",
        "rating": 4.5,
        "tags": ["программист", "хэллоуин"],
        "likes": 95,
        "views": 1100
    }"""

    const val SEARCH_JSON = """{
        "jokes": [
            {
                "id": 100,
                "text": "Программист — это машина, которая превращает кофе в код.",
                "category": "айти",
                "rating": 4.3,
                "tags": ["программист", "кофе"],
                "semantic_score": 0.85
            },
            {
                "id": 101,
                "text": "Жена программиста попросила его сходить в магазин: «Купи батон хлеба. Если будут яйца — возьми десяток». Он принёс 10 батонов.",
                "category": "айти",
                "rating": 4.6,
                "tags": ["программист", "жена"],
                "semantic_score": 0.78
            }
        ],
        "total": 2
    }"""

    const val SEARCH_LIMIT_3_JSON = """{
        "jokes": [
            {
                "id": 200,
                "text": "Шутка 1",
                "category": "айти",
                "rating": 4.0,
                "tags": [],
                "semantic_score": 0.9
            },
            {
                "id": 201,
                "text": "Шутка 2",
                "category": "айти",
                "rating": 4.1,
                "tags": [],
                "semantic_score": 0.8
            },
            {
                "id": 202,
                "text": "Шутка 3",
                "category": "айти",
                "rating": 4.2,
                "tags": [],
                "semantic_score": 0.7
            }
        ],
        "total": 3
    }"""

    const val CONTEXT_RABOTA_JSON = """{
        "jokes": [
            {
                "id": 300,
                "text": "Начальник говорит подчинённому: «Ты опоздал на 40 минут!» — «А вы вчера ушли на 20 минут раньше!» — «Не смей сравнивать меня с собой!» — «И не думаю, вы же вчера украли канцтовары!»",
                "category": "работа",
                "rating": 4.4,
                "tags": ["начальник", "опоздание"],
                "semantic_score": 0.92
            }
        ],
        "matched_categories": ["работа"],
        "context": "работа",
        "search_method": "semantic"
    }"""

    const val CONTEXT_AITI_JSON = """{
        "jokes": [
            {
                "id": 301,
                "text": "— Что такое рекурсия? — Смотри: рекурсия.",
                "category": "айти",
                "rating": 4.2,
                "tags": ["рекурсия", "программист"],
                "semantic_score": 0.88
            }
        ],
        "matched_categories": ["айти"],
        "context": "айти",
        "search_method": "semantic"
    }"""

    const val CONTEXT_KOTIKI_JSON = """{
        "jokes": [
            {
                "id": 302,
                "text": "Кот смотрит на хозяина с осуждением: «Ты почему не на работе? Кормить меня кто будет?»",
                "category": "котики",
                "rating": 4.8,
                "tags": ["кот", "работа"],
                "semantic_score": 0.95
            }
        ],
        "matched_categories": ["котики"],
        "context": "котики",
        "search_method": "semantic"
    }"""

    const val FAVORITES_ADD_JSON = """{"favorites": [1, 42, 100]}"""
    const val FAVORITES_GET_JSON = """{
        "jokes": [
            {
                "id": 42,
                "text": "Программист ставит на тумбочку перед сном два стакана.",
                "category": "айти",
                "rating": 4.7,
                "tags": ["программист"],
                "likes": 128,
                "views": 1540
            },
            {
                "id": 100,
                "text": "Программист — это машина, которая превращает кофе в код.",
                "category": "айти",
                "rating": 4.3,
                "tags": ["программист", "кофе"]
            }
        ]
    }"""
    const val FAVORITES_REMOVE_JSON = """{"favorites": [42]}"""

    const val RATE_JSON = """{"new_rating": 4.4}"""

    const val RATE_404_JSON = """{"detail": "Joke not found"}"""

    const val LIKE_JSON = """{"liked": true}"""

    const val USER_JOKE_CREATE_JSON = """{"id": 5001, "status": "pending_approval"}"""
    const val USER_JOKES_LIST_JSON = """{
        "jokes": [
            {
                "id": 5001,
                "user_id": "anonymous",
                "category": "айти",
                "text": "Мой собственный анекдот про программистов.",
                "rating": 4.0,
                "tags": ["программист"],
                "approved": 0
            }
        ]
    }"""
    const val USER_JOKE_DELETE_JSON = """{"deleted": true}"""

    const val EN_JOKES_JSON = """{
        "jokes": [
            {
                "id": 8001,
                "text": "Why do programmers prefer dark mode? Because light attracts bugs.",
                "category": "en_it",
                "rating": 4.6,
                "tags": ["programming", "dark-mode"]
            }
        ],
        "total": 15
    }"""

    const val SOCIAL_TOP_JSON = """{
        "jokes": [
            {
                "id": 42,
                "text": "Лучший анекдот дня.",
                "category": "айти",
                "rating": 4.9,
                "tags": ["best"],
                "likes": 500,
                "views": 10000
            }
        ],
        "period": "day"
    }"""

    const val TTS_JSON = """{
        "text": "Текст анекдота для озвучки",
        "audio_file": "/data/tts/0d1f0099d439.mp3",
        "duration_estimate": "2 сек",
        "generator": "gTTS (Google TTS, free)"
    }"""

    const val GENERATE_JSON = """{
        "joke": {
            "id": 99999,
            "text": "Сгенерированный анекдот про программиста.",
            "rating": 4.5,
            "tags": ["ai-generated", "llm"],
            "category": "айти",
            "generated": true,
            "generator": "llm"
        },
        "matched_categories": ["айти"]
    }"""

    const val PERSONALIZE_POST_JSON = """{"status": "updated"}"""
    const val PERSONALIZE_GET_JSON = """{
        "jokes": [
            {
                "id": 42,
                "text": "Персонализированный анекдот.",
                "category": "айти",
                "rating": 4.7,
                "tags": ["айти"]
            }
        ]
    }"""

    const val ANALYTICS_STATS_JSON = """{
        "total_events": 5420,
        "unique_users": 328,
        "top_categories": [
            {"category": "айти", "cnt": 1200},
            {"category": "работа", "cnt": 980},
            {"category": "семья", "cnt": 760}
        ]
    }"""

    const val ANALYTICS_POPULAR_JSON = """{
        "popular": [
            {"category": "айти", "cnt": 45},
            {"category": "работа", "cnt": 38},
            {"category": "котики", "cnt": 22}
        ],
        "period_days": 7
    }"""

    const val AD_JSON = """{
        "ad": {
            "type": "banner",
            "text": "📢 Хочешь больше анекдотов? Попробуй Premium!",
            "link": "#premium",
            "show": true
        }
    }"""

    const val PREMIUM_JSON = """{
        "is_premium": false,
        "features": ["unlimited_generation", "no_ads", "exclusive_jokes"],
        "price": "199₽/мес"
    }"""

    const val ERROR_400_JSON = """{"detail": "text не может быть пустым"}"""

    const val SEARCH_EMPTY_JSON = """{"jokes": [], "total": 0}"""

    //endregion

    fun createMockWebServer(): MockWebServer {
        val server = MockWebServer()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                val path = request.path ?: return MockResponse().setResponseCode(404)
                return when {
                    // Stats
                    path == "/api/stats" -> MockResponse()
                        .setBody(STATS_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Categories
                    path == "/api/categories" -> MockResponse()
                        .setBody(CATEGORIES_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Random joke
                    path == "/api/joke/random" -> MockResponse()
                        .setBody(RANDOM_JOKE_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Jokes with category
                    path.startsWith("/api/jokes?") && path.contains("category=") -> {
                        val json = when {
                            path.contains("category=%D0%B0%D0%B9%D1%82%D0%B8") ||
                            path.contains("category=айти") -> RANDOM_JOKE_AITI_JSON
                            else -> RANDOM_JOKE_JSON
                        }
                        MockResponse()
                            .setBody("""{"jokes": [$json], "total": 1}""")
                            .setHeader("Content-Type", "application/json")
                            .setResponseCode(200)
                    }

                    // Jokes without category
                    path.startsWith("/api/jokes?") -> MockResponse()
                        .setBody("""{"jokes": [$RANDOM_JOKE_JSON], "total": 1}""")
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Search
                    path.startsWith("/api/jokes/search") -> {
                        val json = when {
                            path.contains("limit=3") -> SEARCH_LIMIT_3_JSON
                            path.contains("q=%D0%B0%D1%84%D1%8B%D0%B0%D0%B4%D0%BE%D1%84%D1%8A") ||
                                path.contains("q=xyznonexistent") -> SEARCH_EMPTY_JSON
                            else -> SEARCH_JSON
                        }
                        MockResponse()
                            .setBody(json)
                            .setHeader("Content-Type", "application/json")
                            .setResponseCode(200)
                    }

                    // Context
                    path == "/api/jokes/context" -> {
                        val body = request.body.readUtf8()
                        val json = when {
                            body.contains("работа") -> CONTEXT_RABOTA_JSON
                            body.contains("айти") -> CONTEXT_AITI_JSON
                            body.contains("котики") -> CONTEXT_KOTIKI_JSON
                            body.contains("\"text\":\"\"") || body.contains("\"text\": \"\"") -> {
                                return MockResponse()
                                    .setBody(ERROR_400_JSON)
                                    .setHeader("Content-Type", "application/json")
                                    .setResponseCode(400)
                            }
                            else -> CONTEXT_RABOTA_JSON
                        }
                        MockResponse()
                            .setBody(json)
                            .setHeader("Content-Type", "application/json")
                            .setResponseCode(200)
                    }

                    // Generate
                    path == "/api/jokes/generate" -> MockResponse()
                        .setBody(GENERATE_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Favorites
                    path == "/api/favorites" -> {
                        when (request.method) {
                            "POST" -> MockResponse()
                                .setBody(FAVORITES_ADD_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                            "GET" -> MockResponse()
                                .setBody(FAVORITES_GET_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                            else -> MockResponse().setResponseCode(405)
                        }
                    }

                    path.matches(Regex("/api/favorites/\\d+")) -> MockResponse()
                        .setBody(FAVORITES_REMOVE_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Rate
                    path == "/api/rate" -> {
                        val body = request.body.readUtf8()
                        if (body.contains("999999")) {
                            MockResponse()
                                .setBody(RATE_404_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(404)
                        } else {
                            MockResponse()
                                .setBody(RATE_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                        }
                    }

                    // Like
                    path.matches(Regex("/api/jokes/\\d+/like")) -> MockResponse()
                        .setBody(LIKE_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // User jokes
                    path == "/api/user-jokes" -> {
                        when (request.method) {
                            "POST" -> MockResponse()
                                .setBody(USER_JOKE_CREATE_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                            "GET" -> MockResponse()
                                .setBody(USER_JOKES_LIST_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                            else -> MockResponse().setResponseCode(405)
                        }
                    }

                    path.matches(Regex("/api/user-jokes/\\d+")) -> MockResponse()
                        .setBody(USER_JOKE_DELETE_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // English jokes
                    path.startsWith("/api/jokes/en") -> MockResponse()
                        .setBody(EN_JOKES_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Social top
                    path.startsWith("/api/jokes/social/top") -> MockResponse()
                        .setBody(SOCIAL_TOP_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // TTS
                    path == "/api/voice/tts" -> MockResponse()
                        .setBody(TTS_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Personalize
                    path.matches(Regex("/api/personalize/.*")) -> {
                        when (request.method) {
                            "POST" -> MockResponse()
                                .setBody(PERSONALIZE_POST_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                            "GET" -> MockResponse()
                                .setBody(PERSONALIZE_GET_JSON)
                                .setHeader("Content-Type", "application/json")
                                .setResponseCode(200)
                            else -> MockResponse().setResponseCode(405)
                        }
                    }

                    // Analytics
                    path == "/api/analytics/stats" -> MockResponse()
                        .setBody(ANALYTICS_STATS_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    path.startsWith("/api/analytics/popular") -> MockResponse()
                        .setBody(ANALYTICS_POPULAR_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    // Monetization
                    path == "/api/monetization/ad" -> MockResponse()
                        .setBody(AD_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    path.startsWith("/api/monetization/premium") -> MockResponse()
                        .setBody(PREMIUM_JSON)
                        .setHeader("Content-Type", "application/json")
                        .setResponseCode(200)

                    else -> MockResponse().setResponseCode(404)
                }
            }
        }
        return server
    }

    fun createRetrofit(server: MockWebServer): retrofit2.Retrofit {
        val moshi = com.squareup.moshi.Moshi.Builder()
            .addLast(com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory())
            .build()
        return retrofit2.Retrofit.Builder()
            .baseUrl(server.url("/"))
            .addConverterFactory(retrofit2.converter.moshi.MoshiConverterFactory.create(moshi))
            .build()
    }

    fun createApi(server: MockWebServer): com.anekdot.vtemu.api.AnekdotApi {
        return createRetrofit(server).create(com.anekdot.vtemu.api.AnekdotApi::class.java)
    }
}
