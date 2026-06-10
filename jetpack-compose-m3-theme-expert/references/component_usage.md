# Consistent Composable Styling & Component Usage

To keep styling consistent across all screens, do not use raw Material components or hardcoded values directly. Wrap baseline components in custom variants that consume theme-specific CompositionLocals and attributes.

---

## 1. Background Containers (JadeBackground & JadeGradientBackground)

Always wrap screen layouts in a custom background composable. This extracts the surface color and tonal elevation from the custom background theme local.

### Standard Surface Background
```kotlin
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.material3.LocalAbsoluteTonalElevation
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

@Composable
fun JadeBackground(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    // Consume from static CompositionLocal LocalBackgroundTheme
    val color = LocalBackgroundTheme.current.color
    val tonalElevation = LocalBackgroundTheme.current.tonalElevation

    Surface(
        color = if (color == Color.Unspecified) Color.Transparent else color,
        tonalElevation = if (tonalElevation == Dp.Unspecified) 0.dp else tonalElevation,
        modifier = modifier.fillMaxSize()
    ) {
        CompositionLocalProvider(LocalAbsoluteTonalElevation provides 0.dp) {
            content()
        }
    }
}
```

### Cached Gradient Background (Draw Phase Deferral)
For pages utilizing top/bottom gradients, draw the brush in the draw phase using `drawWithCache` to avoid recomposition loops.
```kotlin
import androidx.compose.foundation.layout.Box
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

// tan(11.06 degrees) is constant for NowInAndroid style angled gradient
private const val GRADIENT_ANGLE_TAN = 0.19545f

@Composable
fun JadeGradientBackground(
    modifier: Modifier = Modifier,
    gradientColors: GradientColors = LocalGradientColors.current,
    content: @Composable () -> Unit
) {
    Surface(
        color = if (gradientColors.container == Color.Unspecified) Color.Transparent else gradientColors.container,
        modifier = modifier.fillMaxSize()
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .drawWithCache {
                    // Calculate gradient coordinates angled 11 degrees off the vertical axis
                    // Using size.minDimension (Nia pattern) for consistent scaling across screen sizes
                    val offset = size.minDimension * GRADIENT_ANGLE_TAN
                    val start = Offset(size.width / 2 + offset / 2, 0f)
                    val end = Offset(size.width / 2 - offset / 2, size.height)

                    val topGradient = Brush.linearGradient(
                        0f to if (gradientColors.top == Color.Unspecified) Color.Transparent else gradientColors.top,
                        0.72f to Color.Transparent,
                        start = start,
                        end = end
                    )
                    val bottomGradient = Brush.linearGradient(
                        0.25f to Color.Transparent,
                        1f to if (gradientColors.bottom == Color.Unspecified) Color.Transparent else gradientColors.bottom,
                        start = start,
                        end = end
                    )

                    onDrawBehind {
                        drawRect(topGradient)
                        drawRect(bottomGradient)
                    }
                }
        ) {
            content()
        }
    }
}
```

---

## 2. Wrapping Buttons (JadeButton & JadeOutlinedButton)

Wrap Material 3 buttons to force brand-compliant color schemes and custom borders.

```kotlin
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.RowScope
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun JadeButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    contentPadding: PaddingValues = ButtonDefaults.ContentPadding,
    content: @Composable RowScope.() -> Unit
) {
    Button(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        // Override standard colors using the custom JadeTheme accessor rather than raw MaterialTheme
        colors = ButtonDefaults.buttonColors(
            containerColor = JadeTheme.colorScheme.primary,
            contentColor = JadeTheme.colorScheme.onPrimary
        ),
        contentPadding = contentPadding,
        content = content
    )
}

@Composable
fun JadeOutlinedButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit
) {
    OutlinedButton(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        colors = ButtonDefaults.outlinedButtonColors(
            contentColor = JadeTheme.colorScheme.onSurface
        ),
        border = BorderStroke(
            width = 1.dp,
            color = if (enabled) JadeTheme.colors.border else JadeTheme.colors.onSurfaceDisabled.copy(alpha = 0.12f)
        ),
        content = content
    )
}
```

---

## 3. Typography & Spacing Consistency

### Typographic Grid Alignment
Always use standard styles from `JadeTheme.typography` for text labels. Use custom numeric monospaced text styles for numerical values to ensure column alignment in tables:
```kotlin
import androidx.compose.material3.Text
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Monospaced layout for numbers (retains tabular width)
Text(
    text = "$12,450.80",
    style = NumericTextStyle.copy(
        fontSize = 32.sp,
        fontWeight = FontWeight.Bold,
        color = JadeTheme.colorScheme.onSurface
    )
)
```

### Spacing Scale Constraints
Do not hardcode dimensions. Reference tokens from `JadeTheme.spacing` in modifiers to keep margins strictly on the 4px/8px layout grid:
```kotlin
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier

Card(
    modifier = Modifier
        .padding(horizontal = JadeTheme.spacing.spaceLg) // 24.dp margins
        .fillMaxWidth()
) {
    Column(
        modifier = Modifier.padding(JadeTheme.spacing.spaceMd) // 16.dp inner padding
    ) {
        Text("Account balance", style = JadeTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(JadeTheme.spacing.spaceXs)) // 8.dp gap
        // Numerical balance
    }
}
```
