# Marker animation

Prereq: `marker-rendering.md` (draw-only, overshoot room).

## 1. Cost

Each animating `Clustering` marker re-renders its bitmap + `Marker.setIcon` every frame. 20 animating = 20
uploads/frame. Cost = concurrency, not total count.

## 2. Pop-in via stagger queue

Each new marker takes a start delay from a shared queue: slot N starts one interval after the previous.
Concurrency ≈ `springDuration / interval` (~10 for 400 ms / 40 ms), no pin skipped. Cap the wait: a pin that
would wait past the cap appears instantly, so hundreds are all visible within the cap.

```kotlin
private class PopInQueue(private val interval: Duration, private val maxWait: Duration) {
    private var lastStart = TimeSource.Monotonic.markNow() - interval

    fun nextStartDelay(): Duration? {
        val now = TimeSource.Monotonic.markNow()
        val start = maxOf(lastStart + interval, now)
        val delay = start - now
        if (delay > maxWait) return null
        lastStart = start
        return delay
    }
}

@Composable
private fun rememberPopInScale(queue: PopInQueue): Animatable<Float, AnimationVector1D> {
    val startDelay = remember { queue.nextStartDelay() }
    val scale = remember { Animatable(if (startDelay != null) 0f else 1f) }
    if (startDelay != null) {
        LaunchedEffect(scale) {
            delay(startDelay)
            scale.animateTo(1f, spring(Spring.DampingRatioMediumBouncy, Spring.StiffnessMediumLow))
        }
    }
    return scale
}
// val popInQueue = remember { PopInQueue(40.milliseconds, 400.milliseconds) }  // hoisted above Clustering
// TipCenteredLayout(Modifier.scaleOnDraw { popIn.value }) { ... }
```

- Not a fixed "max N concurrent" budget: it skips animation for N+1 onwards, looks inconsistent. Pacing gives
  the same bound with every early marker animated.
- Not staggered data: see `clustering.md` §1 (N reclusters, clusters form/split on screen).

## 3. Selected marker grow

- `animateFloatAsState` to 1.3–1.4, medium-bouncy spring, scaled from the tip (`TransformOrigin(0.5f, 1f)`) so
  the label below stays put.
- Raise it: `ClusteringMarkerProperties(zIndex = 1f)`.
- Size the pin slot for peak scale incl. overshoot.
- Selected marker inside a cluster: camera move may split the cluster first; grow plays once its marker composes.

## 4. Device-tier tuning

Knobs: interval, cap. Without extra deps:
- `ActivityManager.isLowRamDevice()` → skip pop-in (interval 0, `maxWait` 0).
- `Build.VERSION.MEDIA_PERFORMANCE_CLASS >= Build.VERSION_CODES.TIRAMISU` (API 31+ field) → shorter interval or higher cap.
- `androidx.core:core-performance`: same classification with backport, if already used.
Measure first; stagger alone usually suffices.

## 5. Real user complaints

- Pins removed on pan then re-added one per ~50 ms: "pretty hard to deal with". Visibility beats animation:
  cap ~400 ms, never delay data.
- Bounce clipped at bitmap edge looks broken: reserve overshoot room.
- Clusters re-popping every zoom step looks busy on dense maps: accept with the cap, or pop clusters only on first load.
