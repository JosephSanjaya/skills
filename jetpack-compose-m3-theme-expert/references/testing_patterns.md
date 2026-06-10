# Compose Theme Testing Patterns

Verify that custom composition locals and MaterialTheme configurations are set properly across variations.

## 1. Robolectric Theme Unit Test
Tests should verify color matches, theme fallback, and composition local resolution.
```kotlin
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class ThemeTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun verifyThemeColors_darkThemeFalse_dynamicColorFalse() {
        composeTestRule.setContent {
            NiaTheme(
                darkTheme = false,
                disableDynamicTheming = true
            ) {
                // Assert baseline material scheme matching
                assertEquals(LightDefaultColorScheme.primary, MaterialTheme.colorScheme.primary)
                
                // Assert custom locals matching
                val expectedGradients = GradientColors(
                    top = LightDefaultColorScheme.inverseOnSurface,
                    bottom = LightDefaultColorScheme.primaryContainer,
                    container = LightDefaultColorScheme.surface
                )
                assertEquals(expectedGradients, LocalGradientColors.current)
                
                // Assert custom background matching
                val expectedBg = BackgroundTheme(
                    color = LightDefaultColorScheme.surface,
                    tonalElevation = 2.dp
                )
                assertEquals(expectedBg, LocalBackgroundTheme.current)
            }
        }
    }
}
```

## 2. Screenshot Test Integration
Wrap screen screenshot components in custom themes to capture proper styling states:
```kotlin
import androidx.compose.material3.Text
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.captureToImage
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class ButtonScreenshotTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun primaryButton_lightTheme() {
        composeTestRule.setContent {
            NiaTheme(darkTheme = false) {
                PrimaryBrandButton(onClick = {}) {
                    Text("Action")
                }
            }
        }
        
        // Capture and assert screenshot comparison using captureToImage() or library helpers
        composeTestRule.onRoot().captureToImage()
    }
}
```
