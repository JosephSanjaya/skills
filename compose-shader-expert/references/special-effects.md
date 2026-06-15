# Advanced Special Effects and Shader Recipes

A compilation of premium, high-fidelity shader effects implemented across our indexed projects, featuring mathematical breakdowns and optimized AGSL source code.

---

## 1. Glossy Swirling 3D Liquid Background (Highly Recommended)

*   **Source:** Refined and optimized in `@simple-shader`.
*   **Concepts:** Chaotic coordinate warping, heightmap slope normal estimation, 3D Phong specular lighting, and hybrid Canvas particle rendering.
*   **AGSL Shader Source:**
    ```glsl
    uniform float2 resolution;
    uniform float uTime;
    uniform float2 uTouchPos;

    float hash(float2 p) {
        float2 fractP = fract(p * float2(123.34, 456.21));
        return fract(fractP.x * fractP.y + fractP.y * 13.51);
    }

    float noise(float2 p) {
        float2 i = floor(p);
        float2 f = fract(p);
        float2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i + float2(0.0,0.0)), hash(i + float2(1.0,0.0)), u.x),
                   mix(hash(i + float2(0.0,1.0)), hash(i + float2(1.0,1.0)), u.x), u.y);
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
        
        // Touch displacement (liquid push/pull) - branchless
        float2 touchUV = (fragCoord - uTouchPos) / resolution.y;
        float touchDist = length(touchUV) + 0.0001;
        float force = (1.0 - smoothstep(0.0, 0.45, touchDist)) * 0.15;
        p += (touchUV / touchDist) * force;
        
        float timeOffset = uTime * 0.3;
        float2 pWarped = swirlWarp(p * 2.2, timeOffset);
        
        // 3D normal vector estimation via coordinate offset sampling
        float eps = 0.04;
        float hC = noise(pWarped);
        float hL = noise(pWarped - float2(eps, 0.0));
        float hR = noise(pWarped + float2(eps, 0.0));
        float hD = noise(pWarped - float2(0.0, eps));
        float hU = noise(pWarped + float2(0.0, eps));
        float3 normal = normalize(float3(hL - hR, hD - hU, 0.15));
        
        // Color gradient blending
        half3 colorBg = half3(0.04, 0.01, 0.09); // Deep space violet
        half3 colorCyan = half3(0.0, 0.85, 0.8);  // Neon cyan
        half3 colorMagenta = half3(0.92, 0.05, 0.58); // Hot pink
        half3 colorBlue = half3(0.12, 0.18, 0.85);  // Royal blue
        
        half3 liquidColor = mix(colorBg, colorBlue, clamp(hC * 1.6, 0.0, 1.0));
        liquidColor = mix(liquidColor, colorCyan, clamp(sin(pWarped.x + timeOffset) * 0.5 + 0.5, 0.0, 1.0) * hC);
        liquidColor = mix(liquidColor, colorMagenta, clamp(cos(pWarped.y - timeOffset) * 0.5 + 0.5, 0.0, 1.0) * (1.0 - hC) * 0.75);
        
        // 3D Specular Wet Highlights
        float3 lightDir = normalize(float3(0.3, -0.4, 0.85));
        float specular = pow(max(0.0, dot(normal, lightDir)), 32.0) * 0.65;
        liquidColor += half3(specular) * half3(0.92, 0.96, 1.0);
        
        // God Rays (correct Skia 'atan' usage)
        float2 lightSource = float2(0.5 * aspect, -0.2);
        float2 rayUV = (fragCoord / resolution.y) - lightSource;
        float rayDist = length(rayUV);
        float rayAngle = atan(rayUV.y, rayUV.x);
        
        float rays = sin(rayAngle * 8.0 + uTime * 0.7) * 0.35
                   + sin(rayAngle * 18.0 - uTime * 1.2) * 0.2
                   + sin(rayAngle * 4.0 + uTime * 0.35) * 0.45;
        rays = max(0.0, rays);
        float rayFade = exp(-rayDist * 1.5) * uv.y;
        half3 rayColor = half3(0.8, 0.92, 1.0) * rays * rayFade * 0.5;
        
        // Specular Bloom & Touch ripples glow
        float glow = exp(-rayDist * 2.0) * 0.3;
        half3 bloomColor = half3(0.0, 0.85, 0.8) * glow;
        
        float touchGlow = exp(-touchDist * 5.0) * 0.4;
        half3 touchColor = half3(0.0, 0.9, 0.8) * touchGlow;
        
        half3 finalColor = liquidColor + rayColor + bloomColor + touchColor;
        return half4(finalColor, 1.0);
    }
    ```

---

## 2. Topographic Flow Contour Shader

*   **Source:** `DynamicVisualEffectsAGSL` (TopographicFlowShader).
*   **Concepts:** Domain warping sinusoidal deformation, FBM height fields, net lines rendering using `smoothstep()`, and glow halo creation.
*   **AGSL Shader Source:**
    ```glsl
    uniform float2 resolution;
    uniform float  time;
    uniform float4 lineColor;
    uniform float4 bgColor;

    uniform float LINE_DENSITY;
    uniform float LINE_THICKNESS;
    uniform float NOISE_SCALE;
    uniform float NOISE_INTENSITY;
    uniform float GLOW_WIDTH_MULTIPLIER;
    uniform float GLOW_CONTRAST;
    uniform float SPEED_X;
    uniform float SPEED_Y;

    float hash21(float2 p) {
        return fract(sin(dot(p, float2(12.9898,78.233))) * 43758.5453);
    }

    float noise(float2 p) {
        float2 i = floor(p);
        float2 f = fract(p);
        float a = hash21(i);
        float b = hash21(i + float2(1.0, 0.0));
        float c = hash21(i + float2(0.0, 1.0));
        float d = hash21(i + float2(1.0, 1.0));
        float2 u = f*f*(3.0 - 2.0*f);
        return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
    }

    float fbm(float2 p) {
        float f = 0.0;
        float amp = 0.5;
        for (int i = 0; i < 5; i++) {
            f += noise(p) * amp;
            p *= 2.0;
            amp *= 0.5;
        }
        return f;
    }

    float2 smoothSineWarp(float2 uv, float t) {
        float2 dir;
        dir.x = sin(uv.y * 5.0 + t * SPEED_X);
        dir.y = cos(uv.x * 3.0 + t * SPEED_Y);
        return uv + dir * 0.4;
    }

    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution.xy;
        uv.x *= resolution.x / resolution.y;
        uv = uv * 2.0 - 1.0;

        float2 warped_uv = smoothSineWarp(uv, time * 0.4);
        warped_uv = smoothSineWarp(warped_uv, time * 0.7);

        float h_noise = fbm(warped_uv * NOISE_SCALE);
        float h = warped_uv.y * LINE_DENSITY + h_noise * NOISE_INTENSITY;
        float dist = abs(fract(h) - 0.5);

        // Double Pass: Crisp outline + wide soft glow
        float lineFactor = 1.0 - smoothstep(0.0, LINE_THICKNESS, dist);
        lineFactor = pow(lineFactor, 10.0);

        float glowFactor = 1.0 - smoothstep(0.0, LINE_THICKNESS * GLOW_WIDTH_MULTIPLIER, dist);
        glowFactor = pow(glowFactor, GLOW_CONTRAST);

        float finalFactor = clamp(lineFactor + glowFactor * 0.5, 0.0, 1.0);
        return mix(bgColor, lineColor, finalFactor);
    }
    ```

---

## 3. Prismatic Holographic Screen Effect

*   **Source:** `DynamicVisualEffectsAGSL` (HolographicEffectBitmapShader).
*   **Concepts:** Post-processing distortion, angle-based Fresnel reflectance, and chromatic aberration (RGB splitting).
*   **AGSL Shader Source:**
    ```glsl
    uniform shader inputShader;
    uniform float2 resolution;
    uniform float uTime;
    uniform float2 uTiltOffset; // Device tilt sensor offsets

    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution;
        
        // Coordinate distortion representing microscopic foil ripples
        float2 offset = float2(
            sin(uv.y * 40.0 + uTime * 2.0) * 0.003,
            cos(uv.x * 40.0 + uTime * 2.0) * 0.003
        ) + uTiltOffset * 0.01;
        
        // Chromatic Aberration: sample R, G, B channels at slightly different offset vectors
        float rChannel = inputShader.eval(fragCoord + offset * resolution * 1.5).r;
        float gChannel = inputShader.eval(fragCoord + offset * resolution).g;
        float bChannel = inputShader.eval(fragCoord + offset * resolution * 0.5).b;
        float alpha = inputShader.eval(fragCoord + offset * resolution).a;
        
        half3 baseColor = half3(rChannel, gChannel, bChannel);
        
        // Prismatic holographic overlay (rainbow color gradient mapping)
        float hue = fract(uv.x - uv.y + dot(uTiltOffset, float2(1.0)) + uTime * 0.05);
        half3 rainbow = sin(half3(hue * 6.283) + half3(0.0, 2.0, 4.0)) * 0.5 + 0.5;
        
        // Blend photo content with holographic sheen
        half3 finalColor = mix(baseColor, rainbow, 0.25 + 0.15 * sin(uTime));
        return half4(finalColor * alpha, alpha);
    }
    ```

---

## 4. Multi-Wave Touch Ripple (Displacement Filter)

*   **Source:** `DynamicVisualEffectsAGSL` (WaterEffectBitmapShader).
*   **Concepts:** Post-processing displacement using an array of active touch waves, damping over time, and filtering.
*   **AGSL Shader Source:**
    ```glsl
    uniform shader inputShader;
    uniform float2 uResolution;
    uniform float uTime;

    const int MAX_WAVES = 20;
    uniform int uNumWaves;
    uniform float2 uWaveOrigins[MAX_WAVES];
    uniform float uWaveAmplitudes[MAX_WAVES];
    uniform float uWaveFrequencies[MAX_WAVES];
    uniform float uWaveSpeeds[MAX_WAVES];
    uniform float uWaveStartTimes[MAX_WAVES];
    uniform float uGlobalDamping;
    uniform float uMinAmplitudeThreshold;

    float PI = 3.14159265;

    half4 main(float2 fragCoord) {
        float2 totalOffset = float2(0.0);

        for (int i = 0; i < MAX_WAVES; i++) {
            if (i >= uNumWaves) continue;
            
            float elapsed = uTime - uWaveStartTimes[i];
            float2 diff = fragCoord - uWaveOrigins[i];
            float distance = length(diff);
            float waveFront = uWaveSpeeds[i] * elapsed;
            float relDist = distance - waveFront;

            // Skip wave if it hasn't expanded to current pixel coordinates yet
            if (relDist > 0.0) continue;

            float currentAmplitude = uWaveAmplitudes[i] * pow(uGlobalDamping, elapsed);
            if (currentAmplitude < uMinAmplitudeThreshold) continue;

            // Calculate sinusoidal phase displacement
            float omega = uWaveFrequencies[i] * 2.0 * PI;
            float k = omega / uWaveSpeeds[i];
            float phase = k * distance - omega * elapsed;
            float waveEffect = sin(phase) * currentAmplitude;

            float2 direction = float2(0.0);
            if (distance > 0.0) {
                direction = diff / distance;
            }
            totalOffset += direction * waveEffect;
        }

        // Fetch back-buffer pixel with displacement offset
        return inputShader.eval(fragCoord + totalOffset);
    }
    ```
