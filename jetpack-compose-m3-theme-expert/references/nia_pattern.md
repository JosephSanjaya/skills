# NiaTheme Pattern Reference

NIA design system extends M3 with custom attributes (Gradients, Tonal Elevation, Tinting). Avoids parameter drilling via CompositionLocal.

## 1. Custom Asset Classes
```kotlin
@Immutable
data class GradientColors(
    val top: Color = Color.Unspecified,
    val bottom: Color = Color.Unspecified,
    val container: Color = Color.Unspecified
)

@Immutable
data class BackgroundTheme(
    val color: Color = Color.Unspecified,
    val tonalElevation: Dp = Dp.Unspecified
)

@Immutable
data class TintTheme(
    val iconTint: Color = Color.Unspecified
)
```

## 2. Static Composition Locals
```kotlin
val LocalGradientColors = staticCompositionLocalOf { GradientColors() }
val LocalBackgroundTheme = staticCompositionLocalOf { BackgroundTheme() }
val LocalTintTheme = staticCompositionLocalOf { TintTheme() }
```

## 3. Composable NiaTheme Implementation
```kotlin
import android.os.Build
import androidx.annotation.ChecksSdkIntAtLeast
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.surfaceColorAtElevation
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

@Composable
fun NiaTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    androidTheme: Boolean = false,
    disableDynamicTheming: Boolean = true,
    content: @Composable () -> Unit
) {
    val context = LocalContext.current
    val colorScheme = remember(darkTheme, androidTheme, disableDynamicTheming, context) {
        when {
            androidTheme -> if (darkTheme) DarkAndroidColorScheme else LightAndroidColorScheme
            !disableDynamicTheming && supportsDynamicTheming() -> {
                if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
            }
            else -> if (darkTheme) DarkDefaultColorScheme else LightDefaultColorScheme
        }
    }

    val gradientColors = remember(colorScheme, androidTheme, darkTheme, disableDynamicTheming) {
        val emptyGradientColors = GradientColors(container = colorScheme.surfaceColorAtElevation(2.dp))
        val defaultGradientColors = GradientColors(
            top = colorScheme.inverseOnSurface,
            bottom = colorScheme.primaryContainer,
            container = colorScheme.surface
        )
        when {
            androidTheme -> if (darkTheme) DarkAndroidGradientColors else LightAndroidGradientColors
            !disableDynamicTheming && supportsDynamicTheming() -> emptyGradientColors
            else -> defaultGradientColors
        }
    }

    val backgroundTheme = remember(colorScheme, androidTheme, darkTheme) {
        val defaultBackgroundTheme = BackgroundTheme(color = colorScheme.surface, tonalElevation = 2.dp)
        when {
            androidTheme -> if (darkTheme) DarkAndroidBackgroundTheme else LightAndroidBackgroundTheme
            else -> defaultBackgroundTheme
        }
    }

    val tintTheme = remember(colorScheme, androidTheme, darkTheme, disableDynamicTheming) {
        when {
            androidTheme -> TintTheme()
            !disableDynamicTheming && supportsDynamicTheming() -> TintTheme(colorScheme.primary)
            else -> TintTheme()
        }
    }

    CompositionLocalProvider(
        LocalGradientColors provides gradientColors,
        LocalBackgroundTheme provides backgroundTheme,
        LocalTintTheme provides tintTheme
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = NiaTypography,
            content = content
        )
    }
}

@ChecksSdkIntAtLeast(api = Build.VERSION_CODES.S)
fun supportsDynamicTheming() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
```

