package com.example.shaders.samples

import android.graphics.RuntimeShader
import android.os.Build
import androidx.compose.animation.core.withInfiniteAnimationFrameMillis
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.ShaderBrush

@Language("AGSL")
private const val SIMPLEX_WAVE_SHADER = """
    uniform float2 resolution;
    uniform float uTime;

    float3 mod289(float3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    float2 mod289(float2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    float3 permute(float3 x) { return mod289(((x * 34.0) + 1.0) * x); }

    // 2D Simplex Noise
    float snoise(float2 v) {
        const float4 C = float4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
        float2 i  = floor(v + dot(v, C.yy));
        float2 x0 = v - i + dot(i, C.xx);
        float2 i1 = (x0.x > x0.y) ? float2(1.0, 0.0) : float2(0.0, 1.0);
        float4 x12 = x0.xyxy + C.xxzz;
        x12.xy -= i1;
        i = mod289(i);
        float3 p = permute(permute(i.y + float3(0.0, i1.y, 1.0)) + i.x + float3(0.0, i1.x, 1.0));
        float3 m = max(0.5 - float3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
        m = m * m * m * m;
        float3 x = 2.0 * fract(p * C.www) - 1.0;
        float3 h = abs(x) - 0.5;
        float3 ox = floor(x + 0.5);
        float3 a0 = x - ox;
        m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
        float3 g = float3(a0.x * x0.x + h.x * x0.y,
                          a0.y * x12.x + h.y * x12.y,
                          a0.z * x12.z + h.z * x12.w);
        return 130.0 * dot(m, g);
    }

    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution;
        
        // Dynamic octave-based simplex wave displacement
        float n1 = snoise(uv * 3.0 + float2(0.0, uTime * 0.4));
        float n2 = snoise(uv * 6.0 - float2(uTime * 0.2, 0.0));
        float combinedNoise = (n1 * 0.7) + (n2 * 0.3);
        
        // Procedural gradient coloration based on noise
        half3 deepBlue = half3(0.02, 0.08, 0.23);
        half3 brightTeal = half3(0.12, 0.72, 0.65);
        half3 col = mix(deepBlue, brightTeal, combinedNoise * 0.5 + 0.5);
        
        return half4(col, 1.0);
    }
"""

@Composable
fun ProceduralWavesBackground(modifier: Modifier = Modifier) {
    val timeState = remember { mutableFloatStateOf(0f) }
    
    // Driven time update loop (60+ FPS)
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
            .fillMaxSize()
            .drawWithCache {
                // Initialize and cache RuntimeShader and ShaderBrush
                val shader = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    RuntimeShader(SIMPLEX_WAVE_SHADER).apply {
                        setFloatUniform("resolution", size.width, size.height)
                    }
                } else {
                    null
                }
                
                val brush = shader?.let { ShaderBrush(it) }

                onDrawBehind {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && shader != null && brush != null) {
                        // Dynamically update time uniform without triggering recompositions
                        shader.setFloatUniform("uTime", timeState.floatValue)
                        drawRect(brush)
                    } else {
                        // Fallback background color for older APIs
                        drawRect(androidx.compose.ui.graphics.Color.Blue)
                    }
                }
            }
    )
}
