# Clustering (maps-compose-utils + android-maps-utils)

Contents: 1 items handling · 2 `onClusterManager` trap · 3 thresholds · 4 algorithms · 5 stale camera ·
6 cached-icon renderer · 7 cluster click · 8 pitfalls

## 1. What `Clustering` does with `items` (8.x)

```kotlin
LaunchedEffect(itemsState) {
    snapshotFlow { itemsState.value.toList() }.collect { items ->
        clusterManager.clearItems()
        clusterManager.addItems(items)
        clusterManager.cluster()
    }
}
```

- Every `items` change = full recluster (`Dispatchers.Default`) + renderer diff (Main). Change rarely, in batches.
- No `items.take(n)` reveal with growing `n`: N reclusters, and clusters churn (pin appears, then merges into "2").
  Animate per marker instead (`animation.md`).
- Stable immutable list (`ImmutableList`/`PersistentList`) so equal lists don't recluster.
- `ClusterItem` = `position`, `title`, `snippet`, `zIndex`. Data class OK; equality drives marker reuse
  (`StaticCluster` equality = centre + items).
- `DefaultClusterRenderer` keeps markers only for current clusters, reuses unchanged ones, animates split/merge on zoom.

## 2. `onClusterManager`: one-time-setup trap

Runs in a `SideEffect` = **after every recomposition** of `Clustering`. Make it idempotent or guard it:

```kotlin
onClusterManager = { clusterManager ->
    (clusterManager.renderer as? DefaultClusterRenderer<*>)?.minClusterSize = 2   // cheap, idempotent
    if (clusterManager.algorithm !== visibleAreaAlgorithm) {                     // guard: setter reclusters
        clusterManager.algorithm = visibleAreaAlgorithm
    }
}
```

The `algorithm` setter copies all items and reclusters; unguarded = recluster every recomposition.

## 3. Thresholds and label overlap

- `DefaultClusterRenderer.minClusterSize` default **4**: groups of 2–3 render as stacked separate markers (ugly
  with labels). `= 2` merges anything within clustering distance, so unclustered pins are always spaced.
- Distance: `NonHierarchicalDistanceBasedAlgorithm.maxDistanceBetweenClusteredItems` (dp, default 100). Raise for bigger markers.

## 4. Algorithms and large datasets

| Algorithm | Clusters | Use when |
| --- | --- | --- |
| Default `ScreenBasedAlgorithmAdapter(PreCachingAlgorithmDecorator(NonHierarchicalDistanceBasedAlgorithm()))` | All items, precaches zoom ±1 | Small fixed data |
| `NonHierarchicalViewBasedAlgorithm(widthDp, heightDp)` | Only items in a viewport-sized box around camera target; reclusters every camera idle | Hundreds+ items, or data accumulating on pan |
| `GridBasedAlgorithm`, `CentroidNonHierarchicalDistanceBasedAlgorithm` | Alternatives | Specific looks |

Need view-based when: zoom out/in is laggy and markers exist far off-screen. Default gives every cluster on the
planet a marker; with Compose content each = composed view + bitmap.

```kotlin
val density = LocalDensity.current
val areaSize = with(density) { LocalWindowInfo.current.containerSize.toSize().toDpSize() }
val visibleAreaAlgorithm = remember(areaSize) {
    NonHierarchicalViewBasedAlgorithm<MyPin>(
        (areaSize.width.value * 1.5f).roundToInt(),     // margin so edges are ready before you pan there
        (areaSize.height.value * 1.5f).roundToInt(),
    )
}
```

- Compute size outside `GoogleMap { }`. Map can resize → `updateViewSize` + `cluster()`.
- Trade-off: items beyond the margin appear on camera stop, not mid-pan. Widen margin if visible.

## 5. View-based: stale camera gotcha

The algorithm learns the camera target only via `onCameraChange`, called by `ClusterManager.onCameraIdle`
(and once in `setAlgorithm`). maps-compose calls `onCameraIdle` when `cameraPositionState.isMoving` → false.
Items arriving before the first idle (first fetch while camera sits at initial position) cluster around a stale
or `(0,0)` centre → **nothing shows until the user pans**.

Fix: feed the position whenever `Clustering` recomposes. `onClusterManager` (`SideEffect`) runs before the items
`snapshotFlow` reclusters:

```kotlin
onClusterManager = { clusterManager ->
    if (clusterManager.algorithm !== visibleAreaAlgorithm) clusterManager.algorithm = visibleAreaAlgorithm
    visibleAreaAlgorithm.onCameraChange(cameraPositionState.position)
}
```

## 6. Drop Compose content: cached-icon renderer

`clusterItemContent` = composed view + bitmap per visible marker. Few looks (one per category, no label, no
animation) → cached icons are cheaper:

```kotlin
class CategoryPinRenderer(context: Context, map: GoogleMap, manager: ClusterManager<MyPin>, private val icons: PinIcons) :
    DefaultClusterRenderer<MyPin>(context, map, manager) {
    override fun onBeforeClusterItemRendered(item: MyPin, options: MarkerOptions) {
        options.icon(icons.forCategory(item.category))      // one BitmapDescriptor per category, cached
    }
    override fun onClusterItemUpdated(item: MyPin, marker: Marker) {
        marker.setIcon(icons.forCategory(item.category))
    }
}
// val manager = rememberClusterManager<MyPin>()
// LaunchedEffect(manager) { manager?.renderer = CategoryPinRenderer(...); manager?.setAnimation(false) }
// if (manager != null) Clustering(items = pins, clusterManager = manager)
```

Need per-pin labels/animation → keep Compose content; view-based algorithm + capped animations keep it fast.
`setAnimation(false)` also drops the zoom split/merge animation (noticeable with many markers).

## 7. Cluster click to zoom

```kotlin
onClusterClick = { cluster ->
    scope.launch {
        val bounds = LatLngBounds.builder().apply { cluster.items.forEach { include(it.position) } }.build()
        cameraPositionState.animate(CameraUpdateFactory.newLatLngBounds(bounds, paddingPx), durationMs)
    }
    true   // consume; otherwise default info window/centre behaviour runs
}
```

## 8. Pitfalls

- `Clustering` uses `MarkerManager`, which overwrites map click listeners; maps-compose re-attaches via a posted
  runnable. Don't also set listeners in `MapEffect`.
- Cluster markers are recreated on zoom; per-marker `remember` state (entrance animation) reruns. Keep it cheap, capped.
- Size buckets (10+, 20+, 50+…) apply only to default icons; `clusterContent` gets exact `cluster.size`.
