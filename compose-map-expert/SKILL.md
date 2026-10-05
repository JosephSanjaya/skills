---
name: compose-map-expert
description: Expert guidance for Google Maps in Jetpack Compose (maps-compose, maps-compose-utils Clustering, android-maps-utils ClusterManager). Use this whenever the user works on a GoogleMap composable, markers, MarkerComposable, Clustering/clusterItemContent, cluster algorithms, pins that reload/flicker on pan, laggy zoom with many markers, marker animations that freeze or clip, marker labels, anchors, camera/contentPadding with bottom sheets, or fetching map data by visible bounds — even if they only say "the map", "pins", or "markers" without naming the library.
---

# Compose Map Expert

Maps in Compose look like normal Compose but aren't: the map is a native view and markers are **bitmaps**.
Most bugs come from forgetting that. Apply the model below, then open the reference for the symptom.

<mental_model>
1. **Marker = image.** Content is composed off-screen, drawn to a `Bitmap`, handed to the native map, clipped to its size.
   - `MarkerComposable(keys...)`: re-renders only when `keys` change. Animations inside never play.
   - `Clustering` content: live `ComposeView`, re-rendered next frame **only on draw invalidation**. Layout-size changes alone don't reliably re-render.
   - So: animate in draw phase (`drawWithContent { scale/translate }`); reserve layout room for anything drawn past resting size (spring overshoot) or it clips.
2. **Each animating marker re-uploads a bitmap per frame.** Cost = markers animating at once, not total. Stagger and cap.
3. **`Clustering` reclusters from scratch on every `items` change** (`clearItems(); addItems(all); cluster()`). Feed the full list; never drip-feed items to fake an entrance.
4. **Map owns camera and padding.** Use `GoogleMap(contentPadding = …)` + `CameraPositionState`, not `MapEffect { map.setPadding(...) }`.
5. **Fetch per viewport, display cumulative.** Fetch visible bounds on camera idle, merge by stable id, never clear pins on pan.
</mental_model>

<workflow>
1. Match symptom to a reference below; each is self-contained.
2. Check versions (`maps-compose`, `maps-compose-utils`, `android-maps-utils`). Verified on maps-compose 8.6.x / android-maps-utils 5.2.x; `references/sources-and-versions.md` shows how to confirm behaviour from the sources jar.
3. Fix the root cause in the shared place (renderer, algorithm, ViewModel merge), not per call site.
4. Verify with many real markers; small data hides every bug here. Recipes: `references/verification.md`.
</workflow>

| Symptom / task | Reference |
| --- | --- |
| Marker animation freezes, never animates, clips on bounce | `references/marker-rendering.md` |
| Custom pin shape, label under pin, wrong anchor, selected pin on top | `references/marker-rendering.md` |
| Pop-in/entrance, selected-pin grow, "too much animation" | `references/animation.md` |
| Laggy zoom/pan with hundreds+ markers; markers drawn off-screen | `references/clustering.md` |
| Overlapping labels, cluster thresholds, cluster click zoom, custom algorithm/renderer | `references/clustering.md` |
| Pins vanish/reload on pan, duplicates, racing requests, filters vs pans | `references/data-loading.md` |
| Selected pin under sheet/toolbar, camera centring, sheet jumps | `references/camera-and-layout.md` |
| Artifacts, versions, docs, reading library sources | `references/sources-and-versions.md` |
| Proving a fix | `references/verification.md` |

<defaults>
Apply unasked:
- Marker content: fixed, non-zero size (zero throws `IllegalStateException`).
- Marker animations: draw-only, with overshoot margin.
- Stagger animations with a short cap; never hide a large load for long (`references/animation.md`).
- `Clustering(onClusterManager = …)` runs every recomposition: guard one-time setup with an identity check.
- Large/accumulating data: `NonHierarchicalViewBasedAlgorithm`, fed the current camera position.
- Map requests: cancel-previous job, short camera-idle debounce, merge by id.
</defaults>

When done, tell the user which of these rules the fix relied on.
