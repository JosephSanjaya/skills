# Compose Lifecycle & Invalidation for Shaders

Properly integrating AGSL shaders in Jetpack Compose requires hooking into the correct phases of Compose (Composition, Layout, Draw) to maximize performance and ensure smooth animation.

## 1. Triggering Frame-by-Frame Draw Invalidations

Shaders that animate over time (using a `uTime` uniform) must trigger a redraw at the device's native refresh rate (60Hz, 90Hz, 120Hz).

*   **Continuous Animation Loop:** Use `withInfiniteAnimationFrameMillis` inside a `LaunchedEffect` to update a `timeState` float value:
    ```kotlin
    val timeState = remember { mutableFloatStateOf(0f) }
    LaunchedEffect(Unit) {
        val startTime = System.currentTimeMillis()
        while (true) {
            withInfiniteAnimationFrameMillis { frameTime ->
                timeState.floatValue = (frameTime - startTime) / 1000f
            }
        }
    }
    ```
*   **State-driven Redraws:** Read the `timeState.floatValue` inside the `drawBehind` or `drawWithCache` block. Because Compose tracks state reads inside the Draw phase, updating `timeState` will only dirty the draw phase, forcing a redraw *without* triggering recomposition or relayout.

## 2. drawBehind vs drawWithCache

Choose the correct modifier based on resource allocation:

*   **Use `drawBehind`:** For stateless drawing operations where no large memory allocations occur. Reading animating states here is extremely lightweight.
*   **Use `drawWithCache`:** If you need to allocate objects that depend on the container's layout size (e.g. creating custom gradients, allocating intermediate buffers, or recreating sub-brushes). This caches the created resources until the size changes.

## 3. Shader and Brush Lifecycle Cache

To prevent frame drops, allocate and compile the `RuntimeShader` exactly once and cache the brush:

```kotlin
@Composable
fun InteractiveShaderContainer(modifier: Modifier = Modifier) {
    val timeState = remember { mutableFloatStateOf(0f) }
    
    // 1. Compile shader ONCE
    val shader = remember {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            RuntimeShader(SHADER_SOURCE)
        } else {
            null
        }
    }

    // 2. Cache the brush
    val shaderBrush = remember(shader) {
        shader?.let { ShaderBrush(it) }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .drawBehind {
                val time = timeState.floatValue
                if (shader != null && shaderBrush != null) {
                    // 3. Set uniforms on each draw frame
                    shader.setFloatUniform("resolution", size.width, size.height)
                    shader.setFloatUniform("uTime", time)
                    
                    // 4. Draw using cached brush
                    drawRect(shaderBrush)
                }
            }
    )
}
```
