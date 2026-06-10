---
name: jetpack-compose-m3-theme-expert
description: Architect, implement, and optimize Material 3 custom themes in Jetpack Compose. Use this skill whenever the user mentions Android UI design systems, MaterialTheme overrides, dynamic wallpaper-derived colors, custom CompositionLocal providers (like NiaTheme gradients or background tokens), theme recomposition optimization, @Stable/@Immutable state properties, or custom styling validation scripts, even if they only ask about a basic Compose color or shape change.
---

# Jetpack Compose M3 Theme Expert

<triggers>
Triggers on Android UI styling, custom themes, Material 3 components, dynamic theme values, wallpaper color schemes, CompositionLocal configurations, and Compose rendering optimizations.
</triggers>

<instructions>
Construct dynamic-wallpaper-derived schemes with solid fallbacks. Enforce parameter stability via @Immutable annotations. Defer animated values to draw phase. Rely on providesDefault in reusable UI modules. Validate design-md files using scripts.
</instructions>

## 1. Quick Reference Index

<references>
- **NiaTheme & Custom Locals**: [nia_pattern.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/nia_pattern.md)
- **CompositionLocal Mechanics**: [composition_locals.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/composition_locals.md)
- **Monet Dynamic Colors**: [dynamic_colors.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/dynamic_colors.md)
- **Compose Performance Tuning**: [performance_tuning.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/performance_tuning.md)
- **Theme Unit Testing**: [testing_patterns.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/testing_patterns.md)
- **DESIGN.md Theme Translation**: [design_md_mapping.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/design_md_mapping.md)
- **Consistent Component Usage**: [component_usage.md](file:///Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/references/component_usage.md)
</references>

## 2. Core Constraints (Don'ts > Do's)

<rules>
- **DON'T** use `compositionLocalOf` for stable configs (causes heavy snapshot-read checks). Use `staticCompositionLocalOf`.
- **DON'T** hardcode Hex colors inside presentation code. Use `MaterialTheme.colorScheme` or custom CompositionLocal tokens.
- **DON'T** read animated theme colors directly in `Box(Modifier.background(color))`. Use `drawBehind { drawRect(color) }` to skip layout passes.
- **DON'T** pass unstable collections (like standard `List<Color>`) to theme wrappers. Wrap them in `@Immutable` objects.
- **DON'T** nest multiple `CompositionLocalProvider` packages (high memory and GC overhead). Keep layouts flat.
</rules>

## 3. Custom M3 Theme Integration Template

<templates>
```kotlin
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

@Immutable
data class ExtendedColors(val success: Color, val alert: Color)

@Immutable
data class SpacingScale(val small: Dp = 8.dp, val medium: Dp = 16.dp)

val LocalExtendedColors = staticCompositionLocalOf { ExtendedColors(Color.Unspecified, Color.Unspecified) }
val LocalSpacing = staticCompositionLocalOf { SpacingScale() }

@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val context = LocalContext.current
    val colorScheme = remember(darkTheme, dynamicColor, context) {
        val supportsDynamic = dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
        when {
            supportsDynamic && darkTheme -> dynamicDarkColorScheme(context)
            supportsDynamic && !darkTheme -> dynamicLightColorScheme(context)
            darkTheme -> DarkDefaultColorScheme
            else -> LightDefaultColorScheme
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
            typography = AppTypography,
            shapes = AppShapes,
            content = content
        )
    }
}
```
</templates>

## 4. DESIGN.md to Theme Pipeline Verification
Verify specs match theme files using the validation script:
```bash
python3 /Users/jsanjaya/Projects/skills/jetpack-compose-m3-theme-expert/scripts/validate_theme_file.py <path/to/DESIGN.md>
```

<constraints>
Developers must follow this output schema and ensure that generated theme configurations satisfy:
1. Spacing systems must be mapped to 4px/8px multiples only.
2. Hex colors must be mapped to custom local variables, avoiding true black (#000000) for theme canvas.
3. The validation script must be run to verify compliance, and final format outputs should follow this schema.
</constraints>
