# Loading map data by viewport

Contents: 1 bounds · 2 debounce/cancel · 3 merge · 4 replace vs merge · 5 bounds math · 6 imperative VM sketch

## 1. Bounds from the camera

```kotlin
// First bounds once the projection exists
LaunchedEffect(cameraPositionState) {
    snapshotFlow { cameraPositionState.projection?.visibleRegion?.latLngBounds }
        .filterNotNull().take(1).collect(onBoundsChanged)
}
// Then on every camera idle
LaunchedEffect(cameraPositionState) {
    snapshotFlow { cameraPositionState.isMoving }
        .filter { !it }.drop(1)
        .collect { cameraPositionState.projection?.visibleRegion?.latLngBounds?.let(onBoundsChanged) }
}
```

- First bounds may be the default zoomed-out world camera, before animating to the user. Treat as a normal viewport,
  never as "already loaded".
- `visibleRegion` = whole map view, incl. areas under overlays/sheets.

## 2. Debounce and cancel

- Debounce ~200 ms for pans (flings settle), ~500 ms for text search.
- Run the request **inside** a cancel-previous job. Launched in a separate coroutine (e.g. inside
  `sessionScope.launch…`) → cancelling the debounce doesn't cancel the request → responses race.
  `collectLatest`, `mapLatest`, or a `SerialJob` helper all work.
- Network bridge must be cancellable (`suspendCancellableCoroutine`), or stale responses still arrive.

## 3. Merge, don't reset

Replacing `pins` per response clears markers outside the new viewport and recreates the rest: flicker + full
recluster. Merge by stable id:

```kotlin
private fun PersistentList<Pin>.mergedWith(fetched: List<Pin>): PersistentList<Pin> {
    val fetchedIds = fetched.mapTo(HashSet()) { it.id }
    return (filterNot { it.id in fetchedIds } + fetched).toPersistentList()
}
```

- Fetched copies win (fresh data replaces stale).
- Session accumulation OK; cluster only the visible area with `NonHierarchicalViewBasedAlgorithm` (`clustering.md` §4).
  Prune to a region only if memory becomes a real problem.
- No "skip already-loaded areas" via a remembered bounding box: the first world-sized bounds make every later pan
  look loaded → nothing ever fetches again.

## 4. Replace vs merge

Filter/search/category/date change → **replace** (old pins no longer match). Pan → **merge**. A pan landing while a
filter request is pending must not turn the replace into a merge.

Preferred: tag each response with its query; replace when its filter differs from the shown pins' filter. No
mutable flag, so cancellation order can't break it:

```kotlin
private data class PinQuery(val bounds: LatLngBounds, val filter: PinFilter)

combine(boundsFlow.debounce(200.milliseconds), filterFlow) { bounds, filter -> PinQuery(bounds, filter) }
    .collectLatest { query ->                       // cancels the previous request
        val fetched = try { api.pins(query.bounds.expanded(), query.filter) }
        catch (e: CancellationException) { throw e }
        catch (e: Exception) { _uiState.update { it.copy(errorTrigger = it.errorTrigger + 1) }; return@collectLatest }
        _uiState.update { state ->
            val pins = if (query.filter != state.shownFilter) fetched.toPersistentList()
                       else state.pins.mergedWith(fetched)
            state.copy(pins = pins, shownFilter = query.filter)
        }
    }
```

- Catch every non-cancellation exception in the collector. Uncaught `HttpException` (anything beyond `IOException`)
  ends `collectLatest` → map silently stops loading for the screen's life.
- Debounce bounds only, so a filter tap fetches immediately.
- Optional: hide non-matching pins client-side while the replace request is in flight.

Imperative alternative: flag set on replace request, cleared when a response applies
(`if (isPinReplacementPending) fetched else merged`). Valid if every fetch after a filter change uses the new filter.

Empty-result toasts check the merged list, not the latest page.

## 5. Bounds math pitfalls

- `LatLng` clamps latitude, wraps longitude: `LatLng(90.0, 180.0)` stores longitude `-180`. Whole-world request → raw doubles, not `LatLngBounds`.
- Viewports can cross the antimeridian (`southwest.longitude > northeast.longitude`).
- Expand requested bounds slightly (edge pins ready on nudge); round coordinates to fixed precision (cache-friendly).

## 6. Imperative ViewModel sketch

```kotlin
fun onBoundsChanged(bounds: LatLngBounds) { lastBounds = bounds; fetchPins(bounds, debounce = 200.milliseconds) }

private fun fetchPins(bounds: LatLngBounds, debounce: Duration = Duration.ZERO) {
    viewModelScope.launch {
        fetchJob {                       // cancels the previous invocation, including its request
            delay(debounce)
            _uiState.update { it.copy(isLoading = true) }
            repository.pins(bounds.expanded())
                .onSuccess { fetched -> applyPins(fetched) }
                .onFailure { _uiState.update { it.copy(isLoading = false, errorTrigger = it.errorTrigger + 1) } }
        }
    }
}
```

Keep loading indicators subtle: a spinner toggling every pan, or a list emptying and refilling, is what makes a map
feel like it "stutters".
