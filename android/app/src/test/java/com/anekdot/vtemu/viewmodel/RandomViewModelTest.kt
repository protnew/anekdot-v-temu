package com.anekdot.vtemu.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.anekdot.vtemu.api.ApiResponse
import com.anekdot.vtemu.model.*
import com.anekdot.vtemu.repository.AnekdotRepository
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.*

@OptIn(ExperimentalCoroutinesApi::class)
class RandomViewModelTest {

    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var repository: AnekdotRepository
    private lateinit var viewModel: RandomViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        repository = mock()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // ============================================================
    // loadRandom() tests
    // ============================================================
    @Test
    fun `loadRandom updates joke LiveData on success`() = runTest {
        val joke = Joke(id = 42, text = "Тестовый анекдот", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        val observed = viewModel.joke.value
        assertThat(observed).isNotNull()
        assertThat(observed?.id).isEqualTo(42)
        assertThat(observed?.text).isEqualTo("Тестовый анекдот")
        assertThat(viewModel.isLoading.value).isFalse()
        assertThat(viewModel.error.value).isNull()
    }

    @Test
    fun `loadRandom sets error on failure`() = runTest {
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.error("Network error"))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        assertThat(viewModel.joke.value).isNull()
        assertThat(viewModel.error.value).isEqualTo("Network error")
        assertThat(viewModel.isLoading.value).isFalse()
    }

    @Test
    fun `loadRandom with category calls getRandomJokeByCategory`() = runTest {
        val joke = Joke(id = 55, text = "Анекдот про айти", category = "айти", rating = 4.5)
        whenever(repository.getRandomJokeByCategory("айти")).thenReturn(ApiResponse.success(joke))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.loadRandom("айти")
        advanceUntilIdle()

        assertThat(viewModel.joke.value?.category).isEqualTo("айти")
        assertThat(viewModel.joke.value?.id).isEqualTo(55)
    }

    @Test
    fun `loadRandom clears previous error on second call`() = runTest {
        whenever(repository.getRandomJoke())
            .thenReturn(ApiResponse.error("Error"))
            .thenReturn(ApiResponse.success(Joke(id = 1, text = "Т", category = "айти", rating = 4.0)))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()
        assertThat(viewModel.error.value).isEqualTo("Error")

        viewModel.loadRandom()
        advanceUntilIdle()

        assertThat(viewModel.error.value).isNull()
        assertThat(viewModel.joke.value).isNotNull()
    }

    // ============================================================
    // like() tests
    // ============================================================
    @Test
    fun `like sets liked LiveData to true on success`() = runTest {
        val joke = Joke(id = 42, text = "Тест", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))
        whenever(repository.likeJoke(42)).thenReturn(ApiResponse.success(LikeResponse(liked = true)))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.like()
        advanceUntilIdle()

        assertThat(viewModel.liked.value).isTrue()
    }

    @Test
    fun `like sets error on failure`() = runTest {
        val joke = Joke(id = 42, text = "Тест", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))
        whenever(repository.likeJoke(42)).thenReturn(ApiResponse.error("Like failed"))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.like()
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Like failed")
    }

    @Test
    fun `like does nothing when joke is null`() = runTest {
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.error("No joke"))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.like()
        advanceUntilIdle()

        verify(repository, never()).likeJoke(any())
    }

    // ============================================================
    // rate() tests
    // ============================================================
    @Test
    fun `rate updates newRating on success`() = runTest {
        val joke = Joke(id = 42, text = "Тест", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))
        whenever(repository.rateJoke(42, 5)).thenReturn(ApiResponse.success(RatingResponse(newRating = 4.85)))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.rate(5)
        advanceUntilIdle()

        assertThat(viewModel.newRating.value).isEqualTo(4.85)
    }

    @Test
    fun `rate updates joke rating locally`() = runTest {
        val joke = Joke(id = 42, text = "Тест", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))
        whenever(repository.rateJoke(42, 5)).thenReturn(ApiResponse.success(RatingResponse(newRating = 4.85)))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.rate(5)
        advanceUntilIdle()

        assertThat(viewModel.joke.value?.rating).isEqualTo(4.85)
    }

    @Test
    fun `rate sets error on failure`() = runTest {
        val joke = Joke(id = 42, text = "Тест", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))
        whenever(repository.rateJoke(42, 3)).thenReturn(ApiResponse.error("Rate error"))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.rate(3)
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Rate error")
    }

    // ============================================================
    // textToSpeech() tests
    // ============================================================
    @Test
    fun `textToSpeech sets ttsAudioFile on success`() = runTest {
        val joke = Joke(id = 42, text = "Текст для озвучки", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))
        whenever(repository.textToSpeech("Текст для озвучки"))
            .thenReturn(ApiResponse.success(TtsResponse(
                text = "Текст для озвучки",
                audioFile = "/data/tts/test.mp3",
                durationEstimate = "2 сек",
                generator = "gTTS"
            )))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.textToSpeech()
        advanceUntilIdle()

        assertThat(viewModel.ttsAudioFile.value).isEqualTo("/data/tts/test.mp3")
    }

    // ============================================================
    // share() tests
    // ============================================================
    @Test
    fun `share sets shareText`() = runTest {
        val joke = Joke(id = 42, text = "Тестовый анекдот", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.share()
        advanceUntilIdle()

        assertThat(viewModel.shareText.value).contains("Тестовый анекдот")
        assertThat(viewModel.shareText.value).contains("Анекдот в Тему")
    }

    // ============================================================
    // clearError() and clearShareText() tests
    // ============================================================
    @Test
    fun `clearError clears error`() = runTest {
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.error("Error"))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()
        assertThat(viewModel.error.value).isEqualTo("Error")

        viewModel.clearError()
        assertThat(viewModel.error.value).isNull()
    }

    @Test
    fun `clearShareText clears shareText`() = runTest {
        val joke = Joke(id = 42, text = "Тест", category = "айти", rating = 4.7)
        whenever(repository.getRandomJoke()).thenReturn(ApiResponse.success(joke))

        viewModel = RandomViewModel(repository)
        advanceUntilIdle()

        viewModel.share()
        viewModel.clearShareText()
        assertThat(viewModel.shareText.value).isNull()
    }
}
