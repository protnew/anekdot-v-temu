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
class CategoriesViewModelTest {

    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var repository: AnekdotRepository
    private lateinit var viewModel: CategoriesViewModel

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
    // loadCategories() tests
    // ============================================================
    @Test
    fun `loadCategories on init loads category list`() = runTest {
        val categories = listOf("работа", "айти", "котики", "семья", "деньги")
        whenever(repository.getCategories()).thenReturn(ApiResponse.success(categories))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()

        assertThat(viewModel.categories.value).hasSize(5)
        assertThat(viewModel.categories.value).contains("работа")
        assertThat(viewModel.categories.value).contains("айти")
        assertThat(viewModel.categories.value).contains("котики")
        assertThat(viewModel.isLoading.value).isFalse()
        assertThat(viewModel.error.value).isNull()
    }

    @Test
    fun `loadCategories sets error on failure`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.error("Network error"))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Network error")
        assertThat(viewModel.categories.value).isNull()
    }

    @Test
    fun `loadCategories can be refreshed`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.success(listOf("работа")))
            .thenReturn(ApiResponse.success(listOf("работа", "айти")))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()
        assertThat(viewModel.categories.value).hasSize(1)

        viewModel.loadCategories()
        advanceUntilIdle()
        assertThat(viewModel.categories.value).hasSize(2)
    }

    // ============================================================
    // loadByCategory() tests
    // ============================================================
    @Test
    fun `loadByCategory loads jokes for category`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.success(listOf("айти")))
        val jokes = listOf(
            Joke(id = 55, text = "Почему программисты путают", category = "айти", rating = 4.5),
            Joke(id = 56, text = "Ещё один анекдот", category = "айти", rating = 4.3)
        )
        whenever(repository.getJokesByCategory("айти", 20))
            .thenReturn(ApiResponse.success(JokesResponse(jokes, 2)))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()

        viewModel.loadByCategory("айти")
        advanceUntilIdle()

        assertThat(viewModel.selectedCategory.value).isEqualTo("айти")
        assertThat(viewModel.categoryJokes.value).hasSize(2)
        assertThat(viewModel.categoryJokesTotal.value).isEqualTo(2)
        assertThat(viewModel.isLoading.value).isFalse()
    }

    @Test
    fun `loadByCategory sets error on failure`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.success(listOf("айти")))
        whenever(repository.getJokesByCategory("несуществующая", 20))
            .thenReturn(ApiResponse.error("No jokes found"))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()

        viewModel.loadByCategory("несуществующая")
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("No jokes found")
    }

    @Test
    fun `loadByCategory sets selectedCategory`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.success(listOf("работа")))
        whenever(repository.getJokesByCategory("работа", 20))
            .thenReturn(ApiResponse.success(JokesResponse(emptyList(), 0)))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()

        viewModel.loadByCategory("работа")
        advanceUntilIdle()

        assertThat(viewModel.selectedCategory.value).isEqualTo("работа")
    }

    // ============================================================
    // clearSelectedCategory() tests
    // ============================================================
    @Test
    fun `clearSelectedCategory clears selection and jokes`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.success(listOf("айти")))
        whenever(repository.getJokesByCategory("айти", 20))
            .thenReturn(ApiResponse.success(JokesResponse(
                listOf(Joke(id = 1, text = "Т", category = "айти", rating = 4.0)), 1
            )))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()

        viewModel.loadByCategory("айти")
        advanceUntilIdle()
        assertThat(viewModel.selectedCategory.value).isEqualTo("айти")

        viewModel.clearSelectedCategory()
        assertThat(viewModel.selectedCategory.value).isNull()
        assertThat(viewModel.categoryJokes.value).isEmpty()
    }

    // ============================================================
    // clearError() tests
    // ============================================================
    @Test
    fun `clearError clears error`() = runTest {
        whenever(repository.getCategories())
            .thenReturn(ApiResponse.error("Error"))

        viewModel = CategoriesViewModel(repository)
        advanceUntilIdle()
        assertThat(viewModel.error.value).isEqualTo("Error")

        viewModel.clearError()
        assertThat(viewModel.error.value).isNull()
    }
}
