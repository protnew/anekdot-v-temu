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
class SearchViewModelTest {

    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var repository: AnekdotRepository
    private lateinit var viewModel: SearchViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        repository = mock()
        viewModel = SearchViewModel(repository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // ============================================================
    // search() in regular mode
    // ============================================================
    @Test
    fun `search with valid query updates results LiveData`() = runTest {
        val jokes = listOf(
            Joke(id = 100, text = "Программист — машина", category = "айти", rating = 4.3),
            Joke(id = 101, text = "Кофе в код", category = "айти", rating = 4.6)
        )
        whenever(repository.searchJokes("программист"))
            .thenReturn(ApiResponse.success(JokesResponse(jokes, 2)))

        viewModel.search("программист")
        advanceUntilIdle()

        assertThat(viewModel.results.value).hasSize(2)
        assertThat(viewModel.totalResults.value).isEqualTo(2)
        assertThat(viewModel.isLoading.value).isFalse()
        assertThat(viewModel.error.value).isNull()
    }

    @Test
    fun `search with blank query does nothing`() = runTest {
        viewModel.search("")
        advanceUntilIdle()

        verify(repository, never()).searchJokes(any())
        verify(repository, never()).contextSearch(any())
    }

    @Test
    fun `search sets error on failure`() = runTest {
        whenever(repository.searchJokes("тест"))
            .thenReturn(ApiResponse.error("Search failed"))

        viewModel.search("тест")
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Search failed")
        assertThat(viewModel.results.value).isNull()
    }

    // ============================================================
    // search() in context mode
    // ============================================================
    @Test
    fun `contextSearch with text работа returns matched categories`() = runTest {
        val jokes = listOf(
            Joke(id = 300, text = "Анекдот про работу", category = "работа", rating = 4.4)
        )
        val contextResponse = ContextResponse(
            jokes = jokes,
            matchedCategories = listOf("работа"),
            context = "работа",
            searchMethod = "semantic"
        )
        whenever(repository.contextSearch("работа"))
            .thenReturn(ApiResponse.success(contextResponse))

        // Toggle to context mode first
        viewModel.toggleContextMode()
        advanceUntilIdle()

        viewModel.search("работа")
        advanceUntilIdle()

        assertThat(viewModel.results.value).hasSize(1)
        assertThat(viewModel.matchedCategories.value).contains("работа")
    }

    @Test
    fun `contextSearch with text аити returns matched category айти`() = runTest {
        val jokes = listOf(
            Joke(id = 301, text = "Рекурсия", category = "айти", rating = 4.2)
        )
        val contextResponse = ContextResponse(
            jokes = jokes,
            matchedCategories = listOf("айти"),
            context = "айти",
            searchMethod = "semantic"
        )
        whenever(repository.contextSearch("айти"))
            .thenReturn(ApiResponse.success(contextResponse))

        viewModel.toggleContextMode()
        advanceUntilIdle()

        viewModel.search("айти")
        advanceUntilIdle()

        assertThat(viewModel.matchedCategories.value).contains("айти")
    }

    @Test
    fun `contextSearch with text котики returns matched category котики`() = runTest {
        val jokes = listOf(
            Joke(id = 302, text = "Котик", category = "котики", rating = 4.8)
        )
        val contextResponse = ContextResponse(
            jokes = jokes,
            matchedCategories = listOf("котики"),
            context = "котики",
            searchMethod = "semantic"
        )
        whenever(repository.contextSearch("котики"))
            .thenReturn(ApiResponse.success(contextResponse))

        viewModel.toggleContextMode()
        advanceUntilIdle()

        viewModel.search("котики")
        advanceUntilIdle()

        assertThat(viewModel.matchedCategories.value).contains("котики")
    }

    @Test
    fun `contextSearch sets error on failure`() = runTest {
        whenever(repository.contextSearch("тест"))
            .thenReturn(ApiResponse.error("Context error"))

        viewModel.toggleContextMode()
        advanceUntilIdle()

        viewModel.search("тест")
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Context error")
    }

    // ============================================================
    // toggleContextMode
    // ============================================================
    @Test
    fun `toggleContextMode switches mode`() = runTest {
        assertThat(viewModel.isContextMode.value).isFalse()

        viewModel.toggleContextMode()
        assertThat(viewModel.isContextMode.value).isTrue()

        viewModel.toggleContextMode()
        assertThat(viewModel.isContextMode.value).isFalse()
    }

    @Test
    fun `toggleContextMode clears results`() = runTest {
        val jokes = listOf(Joke(id = 1, text = "Т", category = "айти", rating = 4.0))
        whenever(repository.searchJokes("тест"))
            .thenReturn(ApiResponse.success(JokesResponse(jokes, 1)))

        viewModel.search("тест")
        advanceUntilIdle()
        assertThat(viewModel.results.value).hasSize(1)

        viewModel.toggleContextMode()
        assertThat(viewModel.results.value).isEmpty()
        assertThat(viewModel.matchedCategories.value).isEmpty()
    }

    // ============================================================
    // generateJoke()
    // ============================================================
    @Test
    fun `generateJoke returns generated joke`() = runTest {
        val generatedJoke = Joke(
            id = 99999, text = "Сгенерировано", category = "айти",
            rating = 4.5, generated = true, generator = "llm"
        )
        val response = GenerateResponse(generatedJoke, listOf("айти"))
        whenever(repository.generateJoke("айти"))
            .thenReturn(ApiResponse.success(response))

        viewModel.generateJoke("айти")
        advanceUntilIdle()

        assertThat(viewModel.generatedJoke.value).isNotNull()
        assertThat(viewModel.generatedJoke.value?.joke?.generated).isTrue()
    }

    @Test
    fun `generateJoke with blank text does nothing`() = runTest {
        viewModel.generateJoke("")
        advanceUntilIdle()

        verify(repository, never()).generateJoke(any())
    }

    @Test
    fun `generateJoke sets error on failure`() = runTest {
        whenever(repository.generateJoke("тест"))
            .thenReturn(ApiResponse.error("Generate failed"))

        viewModel.generateJoke("тест")
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Generate failed")
    }

    // ============================================================
    // clearError()
    // ============================================================
    @Test
    fun `clearError clears error`() = runTest {
        whenever(repository.searchJokes("тест"))
            .thenReturn(ApiResponse.error("Error"))

        viewModel.search("тест")
        advanceUntilIdle()
        assertThat(viewModel.error.value).isEqualTo("Error")

        viewModel.clearError()
        assertThat(viewModel.error.value).isNull()
    }
}
