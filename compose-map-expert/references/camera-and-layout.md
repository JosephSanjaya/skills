# Camera, padding, surrounding UI

## 1. CameraPositionState and MapEffect

- `rememberCameraPositionState { position = CameraPosition.fromLatLngZoom(target, zoom) }` = source of truth; a
  position in `GoogleMapOptions` is overridden.
- Move: `cameraPositionState.animate(update, durationMs)` (suspend) or `move(update)`.
- Camera ops before map load can be dropped; gate on `onMapLoaded` if needed.
- `MapEffect(keys) { map -> }` = raw `GoogleMap`, experimental, library-owned. Use for gaps in the Compose API
  (one-shot `animateCamera` with callback), never for state the composable manages (padding, listeners, map type).
- `Clustering` lives inside `GoogleMap { }`; compute `LocalWindowInfo`/insets-based sizes outside and pass in.

## 2. contentPadding: centre in the visible area

`GoogleMap(contentPadding = PaddingValues(...))` shifts the camera centre, Google logo, compass. Lets
`newLatLng(pin)` centre the pin in the visible part of the map.

```kotlin
var topOverlayHeight by remember { mutableStateOf(0.dp) }
Column(Modifier.onSizeChanged { topOverlayHeight = with(density) { it.height.toDp() } }.statusBarsPadding()) {
    // search bar, chips...
}
TransactionMap(
    contentPadding = PaddingValues(
        top = topOverlayHeight,
        bottom = if (sheetOpen) sheetPeekHeight else navigationBarHeight,
    ),
)
```

- `onSizeChanged` **before** `statusBarsPadding()` so the height includes the inset.
- Never also `map.setPadding` in `MapEffect`; they fight, camera jumps.
- Animating `contentPadding` moves the camera every frame; change it in one step with the camera animation.

## 3. Bottom sheets over a map

Material 2 `ModalBottomSheetLayout` anchors derive from sheet content height:
- Height changes (shimmer → list) move the half-expanded anchor → sheet jumps. Constant content height (window
  height − status bar), crossfade inner states (`Crossfade(modifier = Modifier.weight(1f))`).
- `show()` on a visible sheet → `Expanded`. Switching selection while open: `hide(); show()` only if `targetValue == Hidden`.
- Keep the last selected item in a local `remember` and render it while the sheet animates away (no blank mid-hide).
- `scrimColor = Color.Transparent` keeps the map visible/active-looking.

M3 `ModalBottomSheet`/`BottomSheetScaffold`: same anchor behaviour, same constant-height rule.

## 4. Pitfalls

- `MapUiSettings`/`MapProperties` are data classes: `remember` or `copy`, else each recomposition pushes new settings.
- `isMyLocationEnabled = true` without permission throws; gate on permission state.
- Styling: `MapStyleOptions` (JSON) or cloud map ID via `googleMapOptionsFactory = { GoogleMapOptions().mapId(id) }`
  (required for `AdvancedMarker`).
