# GPU Performance Optimization in AGSL

Mobile GPUs use Tile-Based Deferred Rendering (TBDR). To achieve 60fps/120fps, shaders must be optimized to minimize registers, texture fetches, and branching.

## 1. Minimizing Register Pressure & Thread Divergence

Mobile fragment shaders run across thousands of hardware threads organized in warps/SIMD groups.

*   **Avoid Loops in Fragment Shaders:** 
    Loops (e.g., iterating over 20+ particles) force compilers to allocate temporary registers. If registers exceed the GPU hardware limits, the GPU spills variables to slower memory, causing dramatic framerate drops.
*   **Hybrid Rendering Pattern:**
    Never render complex particle systems, floating blobs, or multiple independent shapes in a shader loop. Instead:
    1. Render the main continuous fluid/fluid-warp background using an AGSL shader.
    2. Overlay discrete shapes (like twinkling stars or particles) on top using standard Compose Canvas `drawCircle` or `drawPoints` calls. This runs on the GPU's hardware drawing path (batching vertex buffers) and has virtually zero CPU/GPU overhead.

*   **Branchless Programming:**
    Avoid `if-else` branching on non-constant conditions. SIMD threads execute both branches if they diverge, wasting GPU cycles.
    *   *Bad:*
        ```glsl
        if (dist < 0.4) {
            color = green;
        } else {
            color = blue;
        }
        ```
    *   *Good (Branchless):*
        ```glsl
        color = mix(green, blue, step(0.4, dist));
        ```

## 2. Mathematical Optimization Checklist

*   **Avoid complex functions:** Use `pow()` and `exp()` sparingly.
*   **Precision Selection:** Use `half` (16-bit float) instead of `float` (32-bit float) for colors, gradients, and normals to save GPU register files and power. Use `float` only for coordinate mapping or high-precision accumulators (like noise hash constants).
*   **Vector Operations:** Perform calculations in vector chunks (e.g., `float4` or `float2`) rather than scalar components when possible.

## 3. Shader Warmup and Caching

RuntimeShader compilation occurs at runtime on the CPU, causing a noticeable frame drop ("shader jank") the first time it is drawn.

*   **Pre-compilation:** Initialize the `RuntimeShader` instance during layout/creation or in a `remember` block, not inside the frame-by-frame `onDrawBehind` rendering call.
*   **Stateless Brush Allocation:** Cache the `ShaderBrush` using `remember(shader)` to avoid creating a new Brush on every frame draw.
