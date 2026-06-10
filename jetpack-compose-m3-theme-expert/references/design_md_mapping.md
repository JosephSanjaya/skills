# Mapping DESIGN.md to Jetpack Compose M3 Themes

This reference demonstrates how to translate a machine-readable `DESIGN.md` specification (such as [DESIGN_MINIMALIST.md](file:///Users/jsanjaya/Projects/skills/cooking/compose-m3-theme-expert/DESIGN_MINIMALIST.md)) into a clean, optimized, production-ready Jetpack Compose M3 theme using the NiaTheme architectural pattern.

---

## 1. Step-by-Step Translation Workflow

### Step 1: Map Colors to ColorScheme & Custom Extensions
Map the semantic colors from Section 2 of `DESIGN.md` to:
1. **Material 3 standard roles** (`ColorScheme` parameters: `primary`, `surface`, `onSurface`, etc.).
2. **Extended colors class** for non-standard roles (`surface-elevated`, `surface-sunken`, `border`, `on-surface-secondary`, etc.).

```kotlin
import androidx.compose.ui.graphics.Color
import androidx.compose.runtime.Immutable

// Define extended design token class (marked @Immutable for compiler skipping optimization)
@Immutable
data class ExtendedColors(
    val surfaceElevated: Color,
    val surfaceSunken: Color,
    val onSurfaceSecondary: Color,
    val onSurfaceDisabled: Color,
    val border: Color,
    val divider: Color,
    val success: Color,
    val warning: Color,
    val error: Color,
    val info: Color
)
```

### Step 2: Implement Typography Scale
Map Sections 3 of `DESIGN.md` (font families, sizing, line heights, weights) to Compose `Typography` and custom text styles. Force monospaced numeric formatting for numerical values.

```kotlin
import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val InterFontFamily = FontFamily(
    // Map fonts (e.g. Font(R.font.inter_regular), etc.)
    FontFamily.SansSerif
)

val MonospaceFontFamily = FontFamily.Monospace

val JadeTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = InterFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 32.sp,
        lineHeight = 40.sp
    ),
    bodyLarge = TextStyle(
        fontFamily = InterFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = InterFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp
    )
)

// Monospaced TextStyle for numeric alignments (amounts, counters)
val NumericTextStyle = TextStyle(
    fontFamily = MonospaceFontFamily,
    fontSize = 14.sp,
    lineHeight = 20.sp
)
```

### Step 3: Implement Spacing Scale
Map Section 5 spacing variables directly into a custom spacing class:
```kotlin
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

@Immutable
data class SpacingScale(
    val space2xs: Dp = 4.dp,
    val spaceXs: Dp = 8.dp,
    val spaceSm: Dp = 12.dp,
    val spaceMd: Dp = 16.dp,
    val spaceLg: Dp = 24.dp,
    val spaceXl: Dp = 32.dp,
    val space2xl: Dp = 48.dp
)
```

### Step 4: Declare Static Locals & Theme Wrapper
Expose custom extensions via `staticCompositionLocalOf` to prevent snapshot-tracking overhead. Combine standard `MaterialTheme` with custom locals using the provides infix.

```kotlin
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.material3.MaterialTheme

val LocalExtendedColors = staticCompositionLocalOf<ExtendedColors> {
    error("No ExtendedColors provided")
}

val LocalSpacing = staticCompositionLocalOf { SpacingScale() }

// Custom theme object for convenient lookup
object JadeTheme {
    val colorScheme: ColorScheme
        @Composable
        get() = MaterialTheme.colorScheme

    val typography: Typography
        @Composable
        get() = MaterialTheme.typography

    val shapes: Shapes
        @Composable
        get() = MaterialTheme.shapes

    val colors: ExtendedColors
        @Composable
        get() = LocalExtendedColors.current

    val spacing: SpacingScale
        @Composable
        get() = LocalSpacing.current
}
```

---

## 2. Production Theme Wrapper Example (Jade Minimalist)

This block shows the complete theme composable integrating all elements from [DESIGN_MINIMALIST.md](file:///Users/jsanjaya/Projects/skills/cooking/compose-m3-theme-expert/DESIGN_MINIMALIST.md):

```kotlin
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import android.os.Build

private val LightJadeColorScheme = lightColorScheme(
    primary = Color(0xFF4A7C59),
    surface = Color(0xFFFDFBF7),
    onSurface = Color(0xFF1A2F20),
    onPrimary = Color(0xFFFFFFFF)
)

private val DarkJadeColorScheme = darkColorScheme(
    primary = Color(0xFF5EC290),
    surface = Color(0xFF181E1B),
    onSurface = Color(0xFFEBF5F0),
    onPrimary = Color(0xFF181E1B)
)

private val LightExtendedColors = ExtendedColors(
    surfaceElevated = Color(0xFFF5F2EB),
    surfaceSunken = Color(0xFFEBE7DC),
    onSurfaceSecondary = Color(0xFF687D70),
    onSurfaceDisabled = Color(0xFFA8B3AB),
    border = Color(0xFFDFDACB),
    divider = Color(0xFFE6E1D3),
    success = Color(0xFF6E9C77),
    warning = Color(0xFFD1A751),
    error = Color(0xFFCF7067),
    info = Color(0xFF668FB8)
)

private val DarkExtendedColors = ExtendedColors(
    surfaceElevated = Color(0xFF222B27),
    surfaceSunken = Color(0xFF111614),
    onSurfaceSecondary = Color(0xFFA3BCAE),
    onSurfaceDisabled = Color(0xFF586E62),
    border = Color(0xFF2C3A34),
    divider = Color(0xFF202A25),
    success = Color(0xFF7FB88A),
    warning = Color(0xFFE2BC68),
    error = Color(0xFFDF847C),
    info = Color(0xFF7BA4CC)
)

@Composable
fun JadeMinimalistTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColorEnabled: Boolean = false, // Minimalist themes usually prefer static branding
    content: @Composable () -> Unit
) {
    val context = LocalContext.current
    val colorScheme = remember(darkTheme, dynamicColorEnabled, context) {
        val supportsDynamic = dynamicColorEnabled && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
        when {
            supportsDynamic && darkTheme -> dynamicDarkColorScheme(context)
            supportsDynamic && !darkTheme -> dynamicLightColorScheme(context)
            darkTheme -> DarkJadeColorScheme
            else -> LightJadeColorScheme
        }
    }

    val extendedColors = remember(darkTheme) {
        if (darkTheme) DarkExtendedColors else LightExtendedColors
    }
    val spacingScale = remember { SpacingScale() }

    CompositionLocalProvider(
        LocalExtendedColors provides extendedColors,
        LocalSpacing provides spacingScale
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = JadeTypography,
            content = content
        )
    }
}
```
