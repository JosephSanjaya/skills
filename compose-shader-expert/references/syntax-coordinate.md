# AGSL Syntax & Coordinate Mappings

Guidelines for syntax structures, coordinate systems, and math details in AGSL.

## 1. AGSL vs GLSL Differences

AGSL is integrated into Skia's C++ rendering engine. It delegates clipping, anti-aliasing, and geometry transformations to Skia, and executes only fragment shading.

| Feature | AGSL | GLSL |
| :--- | :--- | :--- |
| **Origin** | Top-left `(0, 0)` | Bottom-left `(0, 0)` |
| **Types** | `half`, `half2`, `half3`, `half4` (16-bit float) | `mediump vecX` |
| **Precision** | `float` (32-bit), `half` (16-bit) | `float`, `double` |
| **Textures** | `uniform shader name` | `uniform sampler2D name` |
| **Sampling** | `name.eval(coord)` | `texture(name, uv)` |

## 2. Coordinate Mapping (ShaderToy to AGSL)

Because ShaderToy uses a bottom-left origin and normalized coordinates, and AGSL uses a top-left origin and pixel coordinates:

*   **ShaderToy Normalization:**
    ```glsl
    vec2 uv = fragCoord / iResolution.xy; // [0, 1] range, bottom-left origin
    ```
*   **AGSL Mapping (Pixel coordinates to normalized top-left):**
    ```glsl
    uniform float2 resolution;
    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution;
        // If Y-inversion is needed (for bottom-left shaders):
        uv.y = 1.0 - uv.y;
        ...
    }
    ```

## 3. Uniforms and Color Spaces

Primitive uniforms match Kotlin types. To pass colors, always use `layout(color)`:

```glsl
uniform float time;
uniform float2 resolution;
layout(color) uniform half4 uTintColor; // Automatically converted to active color space
uniform shader inputImage;              // The rendered composable content texture
```

*   **Color Conversion:** Without `layout(color)`, color values (e.g. SRGB/Display-P3) passed from Kotlin will mismatch Skia's internal working space.
*   **Shader Uniforms:** A `uniform shader` represents a child composable or image texture. Sample it using `.eval(coord)` where `coord` is in pixel coordinates, NOT normalized `uv`.

## 4. Premultiplied Alpha

AGSL requires premultiplied alpha. Returning an un-premultiplied color causes dark/white fringes when blending.

*   **Premultiplication Rule:**
    $$C_{premultiplied} = (R \cdot A, G \cdot A, B \cdot A, A)$$
*   **AGSL Implementation:**
    ```glsl
    half4 main(float2 fragCoord) {
        half3 rgb = half3(1.0, 0.5, 0.2);
        half alpha = 0.5;
        // Correct:
        return half4(rgb * alpha, alpha);
        // Incorrect (causes blending artifacts):
        // return half4(rgb, alpha);
    }
    ```
