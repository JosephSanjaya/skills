# Dynamic Color Systems & Wallpaper Extraction

Dynamic color uses the system's wallpaper color to generate harmonious, accessible color schemes (API 31+).

## 1. Monet Color Engine Pipeline
1. **Wallpaper Extract**: System pulls dominant color clusters.
2. **HCT Conversion**: Seed mapped into HCT (Hue, Chroma, Tone) space. Generates 5 tonal palettes (Primary, Secondary, Tertiary, Neutral, Neutral Variant).
3. **Contrast Alignment**: Palettes mapped to standard M3 roles ensuring WCAG 2.2 contrast compliance.

## 2. API 31+ Dynamic Color Mapping
Compose provides `dynamicLightColorScheme` and `dynamicDarkColorScheme` functions:
```kotlin
import android.os.Build
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext

@Composable
fun resolveColorScheme(darkTheme: Boolean): ColorScheme {
    val context = LocalContext.current
    return remember(darkTheme, context) {
        val supportsDynamic = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
        when {
            supportsDynamic && darkTheme -> dynamicDarkColorScheme(context)
            supportsDynamic && !darkTheme -> dynamicLightColorScheme(context)
            darkTheme -> BrandDarkColorScheme
            else -> BrandLightColorScheme
        }
    }
}
```

## 3. Dark Theme Preference & System Sync
Combine user setting flags with `isSystemInDarkTheme()` to decide current state:
```kotlin
@Composable
fun AppTheme(
    themeSetting: ThemeSetting = ThemeSetting.SYSTEM,
    content: @Composable () -> Unit
) {
    val darkTheme = when (themeSetting) {
        ThemeSetting.LIGHT -> false
        ThemeSetting.DARK -> true
        ThemeSetting.SYSTEM -> isSystemInDarkTheme()
    }
    // Theme application logic...
}
```
