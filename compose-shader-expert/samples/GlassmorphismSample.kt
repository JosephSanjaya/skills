package com.example.shaders.samples

import android.graphics.RenderEffect
import android.graphics.RuntimeShader
import android.os.Build
import androidx.compose.animation.core.withInfiniteAnimationFrameMillis
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.dp

@Language("AGSL")
private const val GLASS_SHADER = """
    uniform float2 resolution;
    uniform shader background; // Pre-blurred input texture
    uniform float uTime;
    uniform float uNoiseIntensity;
    uniform float uRefractionOffset;

    float random(float2 uv) {
        return fract(sin(dot(uv, float2(12.9898, 78.233))) * 43758.5453);
    }

    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution;
        
        // 1. High-frequency frosting noise
        float noise = (random(uv + sin(uTime * 0.1)) - 0.5) * uNoiseIntensity;
        
        // 2. Refracted backdrop sampling
        float2 refractedCoords = fragCoord + float2(noise * uRefractionOffset * resolution.x, 0.0);
        half4 color = background.eval(refractedCoords);
        
        // 3. Mix frosted noise grain
        color.rgb += noise;
        
        // Return premultiplied alpha color
        return half4(color.rgb * color.a, color.a);
    }
"""

@Composable
fun PerformantGlassmorphicContainer(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    // 1. Setup continuous time state for noise animation
    val timeState = remember { mutableFloatStateOf(0f) }
    LaunchedEffect(Unit) {
        val startTime = System.currentTimeMillis()
        while (true) {
            withInfiniteAnimationFrameMillis { frameTime ->
                timeState.floatValue = (frameTime - startTime) / 1000f
            }
        }
    }

    Box(
        modifier = modifier
            .size(320.dp, 200.dp)
            .clip(RoundedCornerShape(24.dp))
            // 2. Pre-blur background content using optimized system RenderEffect
            .graphicsLayer {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    renderEffect = RenderEffect.createBlurEffect(
                        30f, 30f, android.graphics.Shader.TileMode.CLAMP
                    ).asComposeRenderEffect()
                }
            }
            // 3. Apply custom AGSL shader for refraction & frosting in draw phase (zero recompositions)
            .drawWithCache {
                val shader = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    RuntimeShader(GLASS_SHADER).apply {
                        setFloatUniform("resolution", size.width, size.height)
                        setFloatUniform("uNoiseIntensity", 0.04f)
                        setFloatUniform("uRefractionOffset", 0.02f)
                    }
                } else {
                    null
                }

                onDrawBehind {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && shader != null) {
                        // Update high-frequency time uniform in draw phase
                        shader.setFloatUniform("uTime", timeState.floatValue)
                    }
                }
            }
            .background(Color.White.copy(alpha = 0.15f)),
        contentAlignment = Alignment.Center
    ) {
        // Foreground content stays sharp and is drawn on top
        content()
    }
}
