package com.anekdot.vtemu.ui

import androidx.recyclerview.widget.RecyclerView
import androidx.test.espresso.Espresso
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions
import androidx.test.espresso.assertion.ViewAssertions
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers
import androidx.test.espresso.matcher.ViewMatchers.*
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.LargeTest
import com.anekdot.vtemu.R
import org.hamcrest.Matchers
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@LargeTest
class MainActivityTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(
        com.anekdot.vtemu.ui.main.MainActivity::class.java
    )

    // ============================================================
    // 1. App launches without crash
    // ============================================================
    @Test
    fun appLaunchesWithoutCrash() {
        // If we get here, the app launched successfully
        onView(withId(R.id.nav_host_fragment))
            .check(matches(isDisplayed()))
    }

    // ============================================================
    // 2. Bottom navigation has 4 tabs
    // ============================================================
    @Test
    fun bottomNavigationHasFourTabs() {
        onView(withId(R.id.bottom_navigation))
            .check(matches(isDisplayed()))

        // Check all 4 navigation items exist
        onView(withId(R.id.nav_random))
            .check(matches(isDisplayed()))
        onView(withId(R.id.nav_search))
            .check(matches(isDisplayed()))
        onView(withId(R.id.nav_categories))
            .check(matches(isDisplayed()))
        onView(withId(R.id.nav_favorites))
            .check(matches(isDisplayed()))
    }

    // ============================================================
    // 3. Random tab shows joke card
    // ============================================================
    @Test
    fun randomTabShowsJokeCard() {
        // Random tab should be selected by default
        onView(withId(R.id.card_joke))
            .check(matches(isDisplayed()))
    }

    // ============================================================
    // 4. Can navigate to all 4 tabs
    // ============================================================
    @Test
    fun canNavigateToSearchTab() {
        onView(withId(R.id.nav_search))
            .perform(ViewActions.click())
        onView(withId(R.id.search_container))
            .check(matches(isDisplayed()))
    }

    @Test
    fun canNavigateToCategoriesTab() {
        onView(withId(R.id.nav_categories))
            .perform(ViewActions.click())
        onView(withId(R.id.categories_container))
            .check(matches(isDisplayed()))
    }

    @Test
    fun canNavigateToFavoritesTab() {
        onView(withId(R.id.nav_favorites))
            .perform(ViewActions.click())
        onView(withId(R.id.favorites_container))
            .check(matches(isDisplayed()))
    }

    @Test
    fun canNavigateBackToRandomTab() {
        // Navigate away first
        onView(withId(R.id.nav_search))
            .perform(ViewActions.click())

        // Navigate back
        onView(withId(R.id.nav_random))
            .perform(ViewActions.click())
        onView(withId(R.id.card_joke))
            .check(matches(isDisplayed()))
    }

    // ============================================================
    // 5. Search: type text → results appear
    // ============================================================
    @Test
    fun searchTypeTextShowsResults() {
        onView(withId(R.id.nav_search))
            .perform(ViewActions.click())

        onView(withId(R.id.search_edit_text))
            .perform(ViewActions.typeText("программист"))
            .perform(ViewActions.pressImeActionButton())

        // Wait for results (may need IdlingResource in real scenario)
        // Check that results RecyclerView or text is visible
        Espresso.onView(ViewMatchers.withId(R.id.search_results_recycler))
            .check(matches(isDisplayed()))
    }

    // ============================================================
    // 6. Categories: grid visible
    // ============================================================
    @Test
    fun categoriesGridVisible() {
        onView(withId(R.id.nav_categories))
            .perform(ViewActions.click())

        onView(withId(R.id.categories_recycler))
            .check(matches(isDisplayed()))
    }

    // ============================================================
    // 7. Favorites: empty state visible initially
    // ============================================================
    @Test
    fun favoritesEmptyStateVisibleInitially() {
        onView(withId(R.id.nav_favorites))
            .perform(ViewActions.click())

        onView(withId(R.id.empty_state_text))
            .check(matches(isDisplayed()))
        onView(withId(R.id.empty_state_text))
            .check(matches(withText(Matchers.containsString("избранн"))))
    }
}
