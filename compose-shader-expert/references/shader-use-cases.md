# Compose Shader Use Cases

Mathematically complete, performant, and clean AGSL implementations for common high-fidelity visual effects.

## 1. Frosted Glassmorphism & Specular Edges

A high-fidelity glass material requires base backdrop blur, procedural noise (frosting), and a specular highlight border.

```glsl
uniform float2 resolution;
uniform shader background; // Pre-blurred input texture
uniform float uNoiseIntensity; // Default: ~0.03
uniform float uRefractionOffset; // Default: ~0.02

// Simple high-frequency noise
float random(float2 uv) {
    return fract(sin(dot(uv, float2(12.9898, 78.233))) * 43758.5453);
}

// Signed Distance Field (SDF) for a rounded rectangle (for borders/corners)
float sdRoundRect(float2 p, float2 size, float rad) {
    float2 d = abs(p) - size + rad;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - rad;
}

half4 main(float2 fragCoord) {
    float2 uv = fragCoord / resolution;
    
    // 1. Frosting (Procedural noise)
    float noise = (random(uv) - 0.5) * uNoiseIntensity;
    
    // 2. Refraction (Distortion)
    float2 distortedCoords = fragCoord + float2(noise * uRefractionOffset * resolution.x, 0.0);
    
    // 3. Sample pre-blurred background
    half4 bgColor = background.eval(distortedCoords);
    
    // Apply frosting grain
    bgColor.rgb += noise;
    
    // 4. Border Specular Highlight using SDF
    float2 halfRes = resolution * 0.5;
    float borderDist = sdRoundRect(fragCoord - halfRes, halfRes - 2.0, 16.0);
    // Draw 1px crisp outline
    float borderMask = smoothstep(-1.0, 0.0, borderDist) - smoothstep(0.0, 1.0, borderDist);
    half4 borderColor = half4(1.0, 1.0, 1.0, 0.4); // White highlight with 40% opacity
    
    // Mix border with background
    half4 finalColor = mix(bgColor, borderColor, borderMask);
    
    // Premultiply alpha
    return half4(finalColor.rgb * finalColor.a, finalColor.a);
}
```

## 2. Liquid Metaballs (Gooey effect)

Liquid merging is accomplished by soft-blurring two elements and thresholding the overlapping alpha fields. A color recovery script prevents boundary darkening.

```glsl
uniform float2 resolution;
uniform shader content; // Soft-blurred input layer containing metaballs
uniform float uThreshold; // Default: ~0.5
layout(color) uniform half4 uTargetColor; // The solid liquid color

half4 main(float2 fragCoord) {
    half4 color = content.eval(fragCoord);
    
    // Threshold the soft alpha field
    if (color.a > uThreshold) {
        // Proper Coloring: Replace blurred/muddy edge pixels with solid target color
        return half4(uTargetColor.rgb * uTargetColor.a, uTargetColor.a);
    } else {
        // Discard pixel output by returning zeroed alpha
        return half4(0.0);
    }
}
```

### Kotlin Setup (Applying the threshold to blurred children)

```kotlin
Box(
    modifier = Modifier
        .graphicsLayer {
            // 1. Soft-blur the child group
            renderEffect = RenderEffect.createBlurEffect(
                60f, 60f, Shader.TileMode.DECAL
            ).asComposeRenderEffect()
        }
        .graphicsLayer {
            // 2. Apply metaball threshold shader
            val shader = RuntimeShader(METABALL_SHADER)
            shader.setFloatUniform("resolution", size.width, size.height)
            shader.setColorUniform("uTargetColor", Color.Blue.toArgb())
            shader.setFloatUniform("uThreshold", 0.5f)
            
            renderEffect = RenderEffect.createRuntimeShaderEffect(
                shader, "content"
            ).asComposeRenderEffect()
        }
) {
    // Interactive children (e.g. circles moving close to each other)
    ...
}
```

## 3. Procedural Noise & Wave Surfaces

Procedural noise provides resolution-independent textures without bitmap assets.

```glsl
uniform float2 resolution;
uniform float uTime;

// 2D Simplex Noise implementation for flowing organic waves
float3 permute(float3 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }

float snoise(float2 v) {
    const float4 C = float4(0.211324865405187,  // (3.0-sqrt(3.0))/6.0
                            0.366025403784439,  // 0.5*(sqrt(3.0)-1.0)
                           -0.577350269189626,  // -1.0 + 2.0 * C.x
                            0.024390243902439); // 1.0 / 41.0
    float2 i  = floor(v + dot(v, C.yy));
    float2 x0 = v - i + dot(i, C.xx);
    float2 i1 = (x0.x > x0.y) ? float2(1.0, 0.0) : float2(0.0, 1.0);
    float4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    float3 p = permute(permute(i.y + float3(0.0, i1.y, 1.0)) + i.x + float3(0.0, i1.x, 1.0));
    float3 m = max(0.5 - float3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
    m = m * m; m = m * m;
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
    
    // Wave displacement using time-varying Simplex Noise
    float noiseVal = snoise(uv * 4.0 + uTime * 0.5);
    
    // Procedural color gradient
    half3 baseColor = half3(0.1, 0.2, 0.4) + noiseVal * 0.2;
    
    return half4(baseColor, 1.0);
}
```
