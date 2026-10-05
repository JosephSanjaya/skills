# Marker rendering

Contents: 1 render model · 2 draw-only animation · 3 overshoot margin · 4 anchors / tip-centred layout ·
5 teardrop shape · 6 labels · 7 z-index · 8 pitfalls

## 1. How each marker API renders

| API | Content → pixels | Re-renders when |
| --- | --- | --- |
| `Marker(icon = BitmapDescriptor)` | You supply the bitmap | New descriptor passed |
| `MarkerComposable(vararg keys) { }` | `rememberComposeBitmapDescriptor` draws once | Any `keys` value changes |
| `Clustering(clusterItemContent / clusterContent)` | `ComposeUiClusterRenderer` hosts an `InvalidatingComposeView` per visible item/cluster | View's **draw** invalidated; re-render next frame (`awaitFrame`) |
| `AdvancedMarker(iconView / pinConfig)` | Native advanced marker (needs map ID) | Native |

- `MarkerComposable` = snapshot. Every look-changing value goes in `keys` (`MarkerComposable(pin.id, isSelected) { … }`). Animation inside is pointless.
- `Clustering` = live only on draw invalidation (`onDescendantInvalidated` → re-render). A size change relayouts,
  but the bitmap is whatever was last drawn → size animations freeze at a random frame.

## 2. Draw-only animation

Animate in draw phase; read the value inside the draw lambda:

```kotlin
private fun Modifier.scaleOnDraw(
    origin: TransformOrigin = TransformOrigin.Center,
    scale: () -> Float,
): Modifier =
    drawWithContent {
        val pivot = Offset(size.width * origin.pivotFractionX, size.height * origin.pivotFractionY)
        scale(scale(), pivot) { this@drawWithContent.drawContent() }
    }

val selectionScale by animateFloatAsState(if (isSelected) 1.35f else 1f, spring(...))
PinIcon(modifier = Modifier.scaleOnDraw(TransformOrigin(0.5f, 1f)) { selectionScale })
```

- Lambda, not value: read happens in draw (no recomposition/frame) and every frame invalidates draw = triggers re-render.
- `graphicsLayer { }` works in normal Compose; `drawWithContent` is the most reliable trigger for the cluster renderer. Prefer it.
- Child following the animation (label under growing pin): translate in draw, or better pick a pivot that needs no
  movement (scale pin from tip, label below tip).

## 3. Overshoot margin (clipping)

Bitmap = exact measured size; drawing outside is cut. `DampingRatioMediumBouncy` (0.5) overshoots ~16% of distance.

- Pop-in 0→1 peaks ~1.16 → ~8% room per side (use 10%).
- Selection 1→1.35 peaks ~1.35 + 0.16 × 0.35 = 1.41 → size the pin slot for that.

```kotlin
private fun Modifier.reserveOvershootSpace(fraction: Float = 0.1f): Modifier =
    layout { measurable, constraints ->
        val placeable = measurable.measure(constraints)
        val marginX = (placeable.width * fraction).roundToInt()
        val marginY = (placeable.height * fraction).roundToInt()
        layout(placeable.width + marginX * 2, placeable.height + marginY * 2) {
            placeable.place(marginX, marginY)
        }
    }
```

Symmetric margin keeps the centre fixed → centre anchor still lands on the location. No room wanted → `DampingRatioLowBouncy`/`NoBouncy`.

## 4. Anchors and tip-centred layout

`anchor` = fraction of the bitmap. Default `Offset(0.5f, 1.0f)` (bottom centre) for `MarkerComposable` and both
`Clustering` anchors. A label below the pin breaks a bottom anchor (location lands under the label). Put the pin
tip at the exact vertical centre so the anchor ignores label height:

```kotlin
@Composable
private fun TipCenteredLayout(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Layout(modifier = modifier.reserveOvershootSpace(), content = content) { measurables, constraints ->
        val loose = constraints.copy(minWidth = 0, minHeight = 0)
        val pin = measurables.first().measure(loose)
        val label = measurables.getOrNull(1)?.measure(loose)
        val half = max(pin.height, label?.height ?: 0)
        val width = max(pin.width, label?.width ?: 0)
        layout(width, half * 2) {
            pin.placeRelative((width - pin.width) / 2, half - pin.height)
            label?.placeRelative((width - label.width) / 2, half)
        }
    }
}
// Clustering(clusterContentAnchor = Offset(0.5f, 0.5f), clusterItemContentAnchor = Offset(0.5f, 0.5f))
```

Same layout for clusters → shared anchor + overshoot margin. Pop-in about the centre grows out of the tip
("drops onto the spot").

## 5. Teardrop pin shape

Circle head + two tangent lines to a tip, tip rounded with a quadratic curve:

```kotlin
private val TeardropShape = GenericShape { size, _ -> addTeardrop(size, tipRounding = 0.3f) }

private fun Path.addTeardrop(size: Size, tipRounding: Float) {
    val r = size.width / 2
    val angle = acos(r / (size.height - r))           // tangent angle; needs height > width
    val angleDeg = Math.toDegrees(angle.toDouble()).toFloat()
    arcTo(Rect(0f, 0f, size.width, size.width), 90f + angleDeg, 360f - 2 * angleDeg, forceMoveTo = true)
    val tip = Offset(r, size.height)
    val right = Offset(r + r * sin(angle), r + r * cos(angle))
    val left = right.copy(x = size.width - right.x)
    val start = lerp(tip, right, tipRounding)
    val end = lerp(tip, left, tipRounding)
    lineTo(start.x, start.y)
    quadraticTo(tip.x, tip.y, end.x, end.y)
    close()
}
```

Icon/cluster count in a top-aligned `Box(size(headDiameter))`. Height ≈ 1.3× width ≈ iOS `MKMarkerAnnotationView`
balloon. Clusters same size as pins (as iOS); bigger clusters pile up on dense maps.

## 6. Labels under pins

- `widthIn(max = ~96.dp)`, `maxLines = 1`, ellipsis; wide labels inflate the bitmap and overlap neighbours.
- Halo for any map style: same `Text` twice, first `TextStyle(drawStyle = Stroke(width, join = StrokeJoin.Round))`
  in surface colour, second filled.
- Labels expose overlap → lower `minClusterSize` (`clustering.md` §3).

## 7. Z-index / per-marker properties

Inside `Clustering` content, `ClusteringMarkerProperties(anchor, zIndex, rotation)` overrides defaults for that
marker (via `SideEffect`). Raise the selected pin:

```kotlin
ClusteringMarkerProperties(zIndex = if (isSelected) 1f else null)
```

## 8. Pitfalls

- Read selection inside the content lambda: `clusterItemContent = { pin -> Pin(pin, isSelected = pin.id == selectedId) }`.
  Baked into the item or captured once → never recomposes → pin never shrinks back on dismiss.
- No Compose overlay positioned via `projection.toScreenLocation` to fake a live marker: it lags the native map
  during pan/zoom (projection updates arrive after the map moved) and draws above every map element. Animate
  inside the marker, draw-only.
- Zero-size content throws `IllegalStateException("...width or height of zero...")`.
- `clip` + `background` fine; shadows/elevation outside bounds clip too → include them in measured size.
- Resources resolve in the hosted composition; theme `CompositionLocal`s work. Wrong colours → wrap in app theme.
- Every distinct visual state = new bitmap. No per-frame state on hundreds of markers at once.
