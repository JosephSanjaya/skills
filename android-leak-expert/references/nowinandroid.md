# Now in Android Project Best Practices Reference

This document highlights real-world, production-grade memory safety and lifecycle patterns extracted from Google's official [Now in Android](file:///Users/jsanjaya/Projects/skills/cooking/leak-expert/nowinandroid) showcase application.

## 1. Standard Flow Collection
All screens in Now in Android collect Flow streams from ViewModels using `collectAsStateWithLifecycle()`, which avoids keeping flow collectors active when the app goes into the background.

```kotlin
// Sourced from feature/bookmarks/impl/src/main/kotlin/com/google/samples/apps/nowinandroid/feature/bookmarks/impl/BookmarksScreen.kt
@Composable
internal fun BookmarksScreen(
    onTopicClick: (String) -> Unit,
    onShowSnackbar: suspend (String, String?) -> Boolean,
    modifier: Modifier = Modifier,
    viewModel: BookmarksViewModel = hiltViewModel(),
) {
    // Collect flow with lifecycle
    val feedState by viewModel.feedUiState.collectAsStateWithLifecycle()
    
    BookmarksScreen(
        feedState = feedState,
        // ...
    )
}
```

---

## 2. Analytics Tracking via DisposableEffect
To trace screen views without lingering callbacks, a one-off `DisposableEffect` is scoped to key events.

```kotlin
// Sourced from core/ui/src/main/kotlin/com/google/samples/apps/nowinandroid/core/ui/AnalyticsExtensions.kt
/**
 * A side-effect which records a screen view event.
 */
@Composable
fun TrackScreenViewEvent(
    screenName: String,
    analyticsHelper: AnalyticsHelper = LocalAnalyticsHelper.current,
) = DisposableEffect(Unit) {
    analyticsHelper.logScreenView(screenName)
    onDispose {} // Empty cleanup is safe since logScreenView is a one-shot call
}
```

---

## 3. Lifecycle-Aware UI Effect Actions
When UI state must be cleared or updated based on terminal lifecycle states (like `ON_STOP` when user navigates away), Now in Android utilizes `LifecycleEventEffect`.

```kotlin
// Sourced from feature/bookmarks/impl/src/main/kotlin/com/google/samples/apps/nowinandroid/feature/bookmarks/impl/BookmarksScreen.kt
@Composable
internal fun BookmarksScreen(
    // ...
    clearUndoState: () -> Unit = {},
) {
    // ...
    
    // Clear temporary UI states when app/screen is stopped
    LifecycleEventEffect(Lifecycle.Event.ON_STOP) {
        clearUndoState()
    }
}
```

---

## 4. Performance Metric Holders Scoped to LocalView
To avoid leaking views when registering metrics or performance holders, Now in Android scopes the metric state holder to the current view using `remember(localView)`:

```kotlin
// Sourced from core/ui/src/main/kotlin/com/google/samples/apps/nowinandroid/core/ui/JankStatsExtensions.kt
@Composable
fun rememberMetricsStateHolder(): Holder {
    val localView = LocalView.current

    // Symmetrically recreate metric holder if view changes
    return remember(localView) {
        PerformanceMetricsState.getHolderForHierarchy(localView)
    }
}

@Composable
fun TrackDisposableJank(
    vararg keys: Any,
    reportMetric: DisposableEffectScope.(state: Holder) -> DisposableEffectResult,
) {
    val metrics = rememberMetricsStateHolder()
    DisposableEffect(metrics, *keys) {
        reportMetric(this, metrics)
    }
}
```
