# CompositionLocal Architectural Reference

## 1. Dynamic (`compositionLocalOf`) vs Static (`staticCompositionLocalOf`)
- **`compositionLocalOf`**: Wraps value in snapshot-aware `MutableState`. Recomposes **only** the exact composables reading `.current` on update. High read cost, low change cost.
- **`staticCompositionLocalOf`**: Bypasses snapshot tracking. Recomposes the **entire** Composable subtree nested under provider when value changes. Zero read cost, high change cost.

| Parameter | staticCompositionLocalOf | compositionLocalOf |
|---|---|---|
| State Tracking | Bypasses snapshot engine | Snapshot-aware `MutableState` |
| Invalidation | Full subtree recomposition | Isolated reader recomposition |
| Optimal Use Case | Stable theme values (colors, shapes) | Transient/rapidly updating values |

## 2. Recomposition Formula
Let $N$ be total nested composables, $U$ be readers of the CompositionLocal ($U \subseteq N$), and $C_s$ be snapshot overhead.
- **Static Invalidation**: $Cost_{static} = O(N)$
- **Dynamic Invalidation**: $Cost_{dynamic} = O(U) + C_s$

Since theme variables change rarely (only dark/light swap, wallpaper swap), the $C_s$ snapshot tracking overhead on every frame render degrades steady-state performance. Use **`staticCompositionLocalOf`** for theme setups.

## 3. Reusable UI Libraries & Theme Propagation
Avoid using `provides` in generic libraries to prevent overriding developer's custom theme definitions higher up. Use `providesDefault` fallback:
```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf

val LocalExtendedColors = staticCompositionLocalOf<ExtendedColors> {
    error("ExtendedColors not provided")
}

@Composable
fun LibraryComponentTheme(
    customColors: ExtendedColors? = null,
    content: @Composable () -> Unit
) {
    // providesDefault respects client overrides from ancestor hierarchy
    CompositionLocalProvider(
        LocalExtendedColors providesDefault (customColors ?: LightExtendedColors)
    ) {
        content()
    }
}
```
