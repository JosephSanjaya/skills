# Jetpack Compose Custom Theme Performance Tuning

Optimize rendering times and maintain 60fps/120fps by managing how state modifications trigger layout updates.

## 1. Parameter Stability Guidelines
Compose compiler skips rendering if parameters are stable.
- **Unstable Parameter Types**: Lists/Collections (e.g., `List<Color>`) are unstable. Classes containing them fail compiler skipping checks.
- **Remedies**:
  1. Wrap collections in `@Immutable` or `@Stable` data classes.
  2. Use KotlinX Immutable Collections (`ImmutableList<Color>`).
```kotlin
import androidx.compose.runtime.Immutable
import androidx.compose.ui.graphics.Color

@Immutable
data class ExtendedColors(
    val success: Color,
    val onSuccess: Color,
    val successContainer: Color,
    val alertGradients: List<Color> // Compiler tags class as unstable unless @Immutable annotated
)
```

## 2. Deferring State Reads to Draw Phase
Theme transitions or animations (e.g., dynamic backgrounds, scrolling elevation) shouldn't trigger recomposition. Use draw phase lambdas to bypass Composition and Layout phases:
```kotlin
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind

// BAD: Recomposes box scope every color update
val animationColor by animateColorAsState(targetValue = currentThemeColor)
Box(modifier = Modifier.background(animationColor))

// GOOD: Bypasses composition/layout, directly draws color in draw phase
val animationColor by animateColorAsState(targetValue = currentThemeColor)
Box(
    modifier = Modifier.drawBehind {
        drawRect(animationColor)
    }
)
```

## 3. Backwards Writes and Lambdas
- **Backwards Write**: Modifying state in composition body after it is read. Triggers infinite recomposition loop. Always modify states in event lambdas or `SideEffect`s.
- **Unstable Lambdas**: Passing raw lambdas to child composables can disrupt skipping. Wrap lambdas using `remember` or use method references.
```kotlin
import androidx.compose.runtime.remember

// BAD: Creates new lambda object on every recomposition pass
val onClick = { viewModel.process(item) }

// GOOD: Memoized across recompositions
val onClick = remember(item) { { viewModel.process(item) } }
```

## 4. Deep Nesting of Providers
Do not nest multiple `CompositionLocalProvider` wrappers. Each nested provider forces map duplication and increases garbage collection overhead. Keep styling structures flat.
