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
class FavoritesViewModelTest {

    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var repository: AnekdotRepository
    private lateinit var viewModel: FavoritesViewModel
    private val testUserId = "test-user-123"

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
    // loadFavorites() tests
    // ============================================================
    @Test
    fun `loadFavorites on init loads empty list`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(emptyList())))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()

        assertThat(viewModel.favorites.value).isEmpty()
        assertThat(viewModel.isEmpty.value).isTrue()
        assertThat(viewModel.isLoading.value).isFalse()
    }

    @Test
    fun `loadFavorites with existing favorites returns jokes`() = runTest {
        val jokes = listOf(
            Joke(id = 42, text = "Избранный анекдот", category = "айти", rating = 4.7),
            Joke(id = 100, text = "Ещё один", category = "работа", rating = 4.3)
        )
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(jokes)))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()

        assertThat(viewModel.favorites.value).hasSize(2)
        assertThat(viewModel.isEmpty.value).isFalse()
    }

    @Test
    fun `loadFavorites sets error on failure`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.error("Load error"))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Load error")
        assertThat(viewModel.isEmpty.value).isTrue()
    }

    @Test
    fun `loadFavorites can be refreshed`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(emptyList())))
            .thenReturn(ApiResponse.success(FavoritesResponse(
                listOf(Joke(id = 42, text = "Т", category = "айти", rating = 4.0))
            )))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()
        assertThat(viewModel.favorites.value).isEmpty()

        viewModel.loadFavorites()
        advanceUntilIdle()
        assertThat(viewModel.favorites.value).hasSize(1)
    }

    // ============================================================
    // removeFavorite() tests
    // ============================================================
    @Test
    fun `removeFavorite removes joke from list`() = runTest {
        val jokes = listOf(
            Joke(id = 42, text = "Анекдот 1", category = "айти", rating = 4.7),
            Joke(id = 100, text = "Анекдот 2", category = "работа", rating = 4.3)
        )
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(jokes)))
        whenever(repository.removeFavorite("42", testUserId))
            .thenReturn(ApiResponse.success(FavoriteIdsResponse(listOf(100))))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()
        assertThat(viewModel.favorites.value).hasSize(2)

        viewModel.removeFavorite("42")
        advanceUntilIdle()

        assertThat(viewModel.favorites.value).hasSize(1)
        assertThat(viewModel.favorites.value?.first()?.id).isEqualTo(100)
    }

    @Test
    fun `removeFavorite sets isEmpty when last item removed`() = runTest {
        val jokes = listOf(
            Joke(id = 42, text = "Единственный", category = "айти", rating = 4.7)
        )
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(jokes)))
        whenever(repository.removeFavorite("42", testUserId))
            .thenReturn(ApiResponse.success(FavoriteIdsResponse(emptyList())))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()
        assertThat(viewModel.isEmpty.value).isFalse()

        viewModel.removeFavorite("42")
        advanceUntilIdle()

        assertThat(viewModel.favorites.value).isEmpty()
        assertThat(viewModel.isEmpty.value).isTrue()
    }

    @Test
    fun `removeFavorite sets error on failure`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(
                listOf(Joke(id = 42, text = "Т", category = "айти", rating = 4.0))
            )))
        whenever(repository.removeFavorite("42", testUserId))
            .thenReturn(ApiResponse.error("Remove failed"))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()

        viewModel.removeFavorite("42")
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Remove failed")
    }

    // ============================================================
    // addFavorite() tests
    // ============================================================
    @Test
    fun `addFavorite calls repository and reloads`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(emptyList())))
            .thenReturn(ApiResponse.success(FavoritesResponse(
                listOf(Joke(id = 42, text = "Т", category = "айти", rating = 4.0))
            )))
        whenever(repository.addFavorite("42", testUserId))
            .thenReturn(ApiResponse.success(FavoriteIdsResponse(listOf(42))))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()

        viewModel.addFavorite("42")
        advanceUntilIdle()

        verify(repository).addFavorite("42", testUserId)
        verify(repository, times(2)).getFavorites(testUserId)
        assertThat(viewModel.favorites.value).hasSize(1)
    }

    @Test
    fun `addFavorite sets error on failure`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.success(FavoritesResponse(emptyList())))
        whenever(repository.addFavorite("42", testUserId))
            .thenReturn(ApiResponse.error("Add failed"))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()

        viewModel.addFavorite("42")
        advanceUntilIdle()

        assertThat(viewModel.error.value).isEqualTo("Add failed")
    }

    // ============================================================
    // clearError() tests
    // ============================================================
    @Test
    fun `clearError clears error`() = runTest {
        whenever(repository.getFavorites(testUserId))
            .thenReturn(ApiResponse.error("Error"))

        viewModel = FavoritesViewModel(repository, testUserId)
        advanceUntilIdle()
        assertThat(viewModel.error.value).isEqualTo("Error")

        viewModel.clearError()
        assertThat(viewModel.error.value).isNull()
    }
}
