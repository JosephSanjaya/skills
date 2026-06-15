package io.github.josephsanjaya.simpleshader

import android.graphics.RuntimeShader
import android.os.Build
import androidx.compose.animation.core.withInfiniteAnimationFrameMillis
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ShaderBrush
import androidx.compose.ui.input.pointer.pointerInput
import org.intellij.lang.annotations.Language
import kotlin.math.cos
import kotlin.math.sin

@Language("AGSL")
private const val LIQUID_GLOW_SHADER = """
    uniform float2 resolution;
    uniform float uTime;
    uniform float2 uTouchPos;

    // Pseudo-random 2D hash
    float hash(float2 p) {
        float2 fractP = fract(p * float2(123.34, 456.21));
        return fract(fractP.x * fractP.y + fractP.y * 13.51);
    }

    // 2D Value Noise
    float noise(float2 p) {
        float2 i = floor(p);
        float2 f = fract(p);
        float2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i + float2(0.0,0.0)), hash(i + float2(1.0,0.0)), u.x),
                   mix(hash(i + float2(0.0,1.0)), hash(i + float2(1.0,1.0)), u.x), u.y);
    }

    // 3-Octave FBM for smooth liquid detail (highly optimized)
    float fbm(float2 p) {
        float v = 0.0;
        float a = 0.5;
        for (int i = 0; i < 3; i++) {
            v += a * noise(p);
            p = float2(p.x * 0.8 + p.y * 0.6, -p.x * 0.6 + p.y * 0.8) * 2.0 + float2(10.0);
            a *= 0.5;
        }
        return v;
    }

    // Swirling trigonometric chaotic feedback loop (oil flow/plasma style)
    float2 swirlWarp(float2 p, float t) {
        float2 warped = p;
        for (int i = 0; i < 3; i++) {
            float len = length(warped);
            warped.x += sin(warped.y + t * 0.4) * 0.6;
            warped.y += cos(warped.x + t * 0.3 + cos(len * 1.5)) * 0.4;
        }
        return warped;
    }

    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution;
        float aspect = resolution.x / resolution.y;
        float2 p = uv;
        p.x *= aspect;
        
        // 1. Touch displacement (liquid push/pull) - branchless
        float2 touchUV = (fragCoord - uTouchPos) / resolution.y;
        float touchDist = length(touchUV) + 0.0001;
        float force = (1.0 - smoothstep(0.0, 0.45, touchDist)) * 0.15;
        p += (touchUV / touchDist) * force;
        
        // 2. Swirling coordinates
        float timeOffset = uTime * 0.3;
        float2 pWarped = swirlWarp(p * 2.2, timeOffset);
        
        // 3. Liquid Height Map & Normal Vector Estimation (for 3D specular shine)
        float eps = 0.04;
        float hC = noise(pWarped);
        float hL = noise(pWarped - float2(eps, 0.0));
        float hR = noise(pWarped + float2(eps, 0.0));
        float hD = noise(pWarped - float2(0.0, eps));
        float hU = noise(pWarped + float2(0.0, eps));
        
        // Normal vector represents surface slope (specular bump)
        float3 normal = normalize(float3(hL - hR, hD - hU, 0.15));
        
        // 4. Liquid Color Gradients (Cyan, magenta/pink, royal blue flowing)
        half3 colorBg = half3(0.04, 0.01, 0.09); // Deep space violet
        half3 colorCyan = half3(0.0, 0.85, 0.8);  // Neon cyan
        half3 colorMagenta = half3(0.92, 0.05, 0.58); // Hot pink
        half3 colorBlue = half3(0.12, 0.18, 0.85);  // Royal blue
        
        half3 liquidColor = mix(colorBg, colorBlue, clamp(hC * 1.6, 0.0, 1.0));
        liquidColor = mix(liquidColor, colorCyan, clamp(sin(pWarped.x + timeOffset) * 0.5 + 0.5, 0.0, 1.0) * hC);
        liquidColor = mix(liquidColor, colorMagenta, clamp(cos(pWarped.y - timeOffset) * 0.5 + 0.5, 0.0, 1.0) * (1.0 - hC) * 0.75);
        
        // 5. 3D Specular Wet Highlights
        float3 lightDir = normalize(float3(0.3, -0.4, 0.85));
        float specular = pow(max(0.0, dot(normal, lightDir)), 32.0) * 0.65;
        liquidColor += half3(specular) * half3(0.92, 0.96, 1.0); // Add gloss/wet highlight
        
        // 6. God Rays (Light shafts radiating down)
        float2 lightSource = float2(0.5 * aspect, -0.2);
        float2 rayUV = (fragCoord / resolution.y) - lightSource;
        float rayDist = length(rayUV);
        float rayAngle = atan(rayUV.y, rayUV.x); // Corrected to use atan(y, x) instead of atan2
        
        float rays = sin(rayAngle * 8.0 + uTime * 0.7) * 0.35
                   + sin(rayAngle * 18.0 - uTime * 1.2) * 0.2
                   + sin(rayAngle * 4.0 + uTime * 0.35) * 0.45;
        rays = max(0.0, rays);
        float rayFade = exp(-rayDist * 1.5) * uv.y;
        half3 rayColor = half3(0.8, 0.92, 1.0) * rays * rayFade * 0.5;
        
        // 7. Specular Bloom & Touch ripples glow
        float glow = exp(-rayDist * 2.0) * 0.3;
        half3 bloomColor = half3(0.0, 0.85, 0.8) * glow;
        
        // Touch glow (bloom) - branchless
        float touchGlow = exp(-touchDist * 5.0) * 0.4;
        half3 touchColor = half3(0.0, 0.9, 0.8) * touchGlow;
        
        // Combine all layers
        half3 finalColor = liquidColor + rayColor + bloomColor + touchColor;
        
        return half4(finalColor, 1.0);
    }
"""

private data class Particle(
    val xPercent: Float,
    val yPercent: Float,
    val speed: Float,
    val size: Float,
    val baseAlpha: Float,
    val angleOffset: Float
)

@Composable
fun InteractiveShaderBackground(modifier: Modifier = Modifier) {
    var touchPos by remember { mutableStateOf(Offset(-9999f, -9999f)) }
    val timeState = remember { mutableFloatStateOf(0f) }

    // Stable particle configuration for all API levels
    val particles = remember {
        List(30) {
            Particle(
                xPercent = Math.random().toFloat(),
                yPercent = Math.random().toFloat(),
                speed = 0.02f + Math.random().toFloat() * 0.03f,
                size = 2.5f + Math.random().toFloat() * 4f,
                baseAlpha = 0.15f + Math.random().toFloat() * 0.35f,
                angleOffset = (Math.random() * Math.PI * 2.0).toFloat()
            )
        }
    }

    LaunchedEffect(Unit) {
        val startTime = System.currentTimeMillis()
        while (true) {
            withInfiniteAnimationFrameMillis { frameTime ->
                timeState.floatValue = (frameTime - startTime) / 1000f
            }
        }
    }

    // Cache shader
    val shader = remember {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            RuntimeShader(LIQUID_GLOW_SHADER)
        } else {
            null
        }
    }

    val shaderBrush = remember(shader) {
        shader?.let { ShaderBrush(it) }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectDragGestures(
                    onDragStart = { offset -> touchPos = offset },
                    onDrag = { change, _ ->
                        change.consume()
                        touchPos = change.position
                    },
                    onDragEnd = { touchPos = Offset(-9999f, -9999f) },
                    onDragCancel = { touchPos = Offset(-9999f, -9999f) }
                )
            }
            .drawBehind {
                val time = timeState.floatValue
                val width = size.width
                val height = size.height
                val minDim = size.minDimension

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && shader != null && shaderBrush != null) {
                    // Render glossy liquid & god rays completely on GPU
                    shader.setFloatUniform("resolution", width, height)
                    shader.setFloatUniform("uTime", time)
                    shader.setFloatUniform("uTouchPos", touchPos.x, touchPos.y)
                    drawRect(shaderBrush)
                } else {
                    // Fallback animated liquid waves for older Android APIs (layers of smooth flowing gradients)
                    val x1 = (0.5f + 0.22f * cos(time * 0.5f)) * width
                    val y1 = (0.5f + 0.18f * sin(time * 0.35f)) * height

                    val x2 = (0.5f + 0.25f * sin(time * 0.45f)) * width
                    val y2 = (0.5f + 0.2f * cos(time * 0.4f)) * height

                    val x3 = (0.5f + 0.3f * cos(time * 0.3f + 1f)) * width
                    val y3 = (0.5f + 0.25f * sin(time * 0.25f - 1f)) * height

                    // Draw deep space base
                    drawRect(Color(0xFF0C0315))

                    // Draw Blob 1 (Cyan)
                    drawRect(
                        Brush.radialGradient(
                            colors = listOf(Color(0xFF00F2FE).copy(alpha = 0.35f), Color.Transparent),
                            center = Offset(x1, y1),
                            radius = minDim * 0.85f
                        )
                    )

                    // Draw Blob 2 (Hot Pink)
                    drawRect(
                        Brush.radialGradient(
                            colors = listOf(Color(0xFFF355DA).copy(alpha = 0.35f), Color.Transparent),
                            center = Offset(x2, y2),
                            radius = minDim * 0.85f
                        )
                    )

                    // Draw Blob 3 (Royal Blue)
                    drawRect(
                        Brush.radialGradient(
                            colors = listOf(Color(0xFF1F35F2).copy(alpha = 0.3f), Color.Transparent),
                            center = Offset(x3, y3),
                            radius = minDim * 0.9f
                        )
                    )

                    // Draw Touch reactive blob
                    if (touchPos.x >= 0f) {
                        drawRect(
                            Brush.radialGradient(
                                colors = listOf(Color(0xFF00F2FE).copy(alpha = 0.25f), Color.Transparent),
                                center = touchPos,
                                radius = minDim * 0.45f
                            )
                        )
                    }
                }

                // Render twinkling & rising particles on top for ALL API levels (highly efficient on CPU)
                particles.forEach { p ->
                    val x = ((p.xPercent + sin(time * 0.4f + p.angleOffset) * 0.05f) % 1.0f + 1.0f) % 1.0f * width
                    val y = ((p.yPercent - time * p.speed) % 1.0f + 1.0f) % 1.0f * height
                    val alphaVal = p.baseAlpha * (0.5f + 0.5f * sin(time * 2.5f + p.angleOffset))

                    drawCircle(
                        color = Color.White,
                        radius = p.size,
                        center = Offset(x, y),
                        alpha = alphaVal
                    )
                }
            }
    )
}
