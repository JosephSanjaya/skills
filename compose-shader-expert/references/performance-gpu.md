# Mobile GPU Shader Optimization

Guidelines for writing branchless, low-precision, and bandwidth-efficient shaders for mobile GPUs (Adreno, Mali).

## 1. Branching Avoidance (Branchless Math)

Mobile GPUs (Tile-Based Deferred Renderers) execute code in SIMD warp groups. If fragments in a warp choose different branches, the GPU executes both branches and masks out the unselected pixels. This doubles instruction cycles.

*   **Rule:** Replace conditional `if-else` blocks with mathematical equivalents.

```glsl
// INCORRECT (Triggers branching):
half4 color;
if (dist < uRadius) {
    color = uInnerColor;
} else {
    color = uOuterColor;
}

// CORRECT (Branchless math):
float edge = step(uRadius, dist);
half4 color = mix(uInnerColor, uOuterColor, edge);
```

### Common Branchless Replacements

*   **Select value based on comparison:** Use `step(a, b)` or `smoothstep(a, b, x)`.
*   **Clamp range:** Use `clamp(x, minVal, maxVal)` instead of checking boundaries.
*   **Conditional color mixing:** Use `mix(colorA, colorB, step(threshold, value))`.

## 2. Precision Management & Register Pressure

Register pressure dictates how many threads can run in parallel on a GPU core. Using 32-bit `float` variables everywhere consumes twice the register space of 16-bit `half` variables, cutting GPU concurrency in half.

*   **Rule:** Default to `half` for all colors, lighting calculations, and texture values. Use `float` only for coordinates, matrices, and time uniforms.

| Variable | Precision | Rationale |
| :--- | :--- | :--- |
| **Coordinates (`uv`, `fragCoord`)** | `float`, `float2` | `half` coordinates cause visual jittering and banding. |
| **Time (`uTime`)** | `float` | `half` precision degrades over time, causing animations to stutter. |
| **Colors (`color`, `tint`)** | `half`, `half4` | `half` is indistinguishable from `float` for 8-bit color outputs. |
| **Normal vectors** | `half3` | 16-bit float is sufficient for surface vectors. |

## 3. Discarding and Early-Z Testing

Avoid using the `discard` keyword. Modern GPUs use Early-Z rejection to skip fragment execution for occluded pixels. Using `discard` forces the GPU to run the shader to determine if a pixel exists, disabling Early-Z and causing high overdraw.

*   **Rule:** Return transparent black `half4(0.0)` instead of `discard`, or use alpha blending to render nothing.

## 4. Bandwidth Limits & Texture Fetches

Texture fetches (calls to `.eval()`) move data from memory to registers, which is a common bottleneck on mobile.

*   **Rule:** Keep the number of calls to `.eval()` below 5 per pass.
*   **Texture Packing:** Pack unrelated values (e.g., noise intensity, roughness, displacement values) into separate channels (R, G, B, A) of a single input image/texture instead of using multiple textures.
*   **Avoid High tap kernels:** Instead of calculating a 17-tap Gaussian blur in AGSL (which requires 17 evaluations), perform the blur using Android's native `RenderEffect.createBlurEffect`, then pass the blurred output to your AGSL shader for refraction/frosting.

## 5. Shader Warm-Up (Compilation Spike)

Shaders are compiled dynamically by the GPU driver when first drawn, which can take up to 80ms, causing noticeable frame drops (jank).

*   **Rule:** Pre-compile/warm up shaders by drawing them offscreen or on a 1x1 pixel layout during app startup or during navigation transitions before they are displayed.
