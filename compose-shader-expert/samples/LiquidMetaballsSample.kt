package com.example.shaders.samples

import android.graphics.RenderEffect
import android.graphics.RuntimeShader
import android.os.Build
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp

@Language("AGSL")
private const val METABALL_SHADER = """
    uniform float2 resolution;
    uniform shader content; // Input texture (blurred circles)
    uniform float uThreshold; // Value to step alpha (typically ~0.5)
    layout(color) uniform half4 uTargetColor;

    half4 main(float2 fragCoord) {
        half4 color = content.eval(fragCoord);
        
        // Threshold the blurred alpha channel
        if (color.a > uThreshold) {
            // Return solid target color to prevent muddy/darkened edges
            return half4(uTargetColor.rgb * uTargetColor.a, uTargetColor.a);
        } else {
            // Fully discard transparent pixels
            return half4(0.0);
        }
    }
"""

@Composable
fun LiquidMetaballsContainer(
    modifier: Modifier = Modifier,
    circleOffsetX: Int,
    circleOffsetY: Int
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.White)
            // 1. Apply offscreen CompositingStrategy and system blur to all children
            .graphicsLayer {
                compositingStrategy = androidx.compose.ui.graphics.CompositingStrategy.Offscreen
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    renderEffect = RenderEffect.createBlurEffect(
                        50f, 50f, android.graphics.Shader.TileMode.DECAL
                    ).asComposeRenderEffect()
                }
            }
            // 2. Apply thresholding AGSL shader in draw phase
            .graphicsLayer {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    val shader = RuntimeShader(METABALL_SHADER).apply {
                        setFloatUniform("resolution", size.width, size.height)
                        setColorUniform("uTargetColor", Color.Magenta.toArgb())
                        setFloatUniform("uThreshold", 0.6f)
                    }
                    renderEffect = RenderEffect.createRuntimeShaderEffect(
                        shader, "content"
                    ).asComposeRenderEffect()
                }
            },
        contentAlignment = Alignment.Center
    ) {
        // Child 1 (Static center)
        Box(
            modifier = Modifier
                .size(100.dp)
                .background(Color.Magenta, CircleShape)
        )
        
        // Child 2 (Dynamic moving circle)
        Box(
            modifier = Modifier
                .offset { IntOffset(circleOffsetX, circleOffsetY) }
                .size(80.dp)
                .background(Color.Magenta, CircleShape)
        )
    }
}
