# Jetpack Compose Integration & Lifecycle

Guidelines for performant shader integration, avoiding recomposition, caching shaders, and multiplatform expect/actual abstractions.

## 1. ShaderBrush vs RenderEffect

*   **ShaderBrush:** Applied directly to drawing commands (`drawRect`, `drawPath`) in a `Canvas` or `drawBehind` modifier. Ideal for procedural backgrounds/patterns. Low overhead.
*   **RenderEffect:** Applied via `Modifier.graphicsLayer { renderEffect = ... }`. Applies post-processing to the entire composable and its children. Requires an offscreen buffer (higher memory and GPU cost).

## 2. Preventing Recomposition (Deferred Reads)

Setting time or touch uniforms at 60/120fps by reading state directly in the Composable function body will trigger full recomposition, ruining performance. 

*   **Deferred Pattern:** Read animated states only inside the lambda blocks of modifiers (such as `graphicsLayer { ... }` or `drawWithCache { ... }`). This bypasses the composition/layout phases, executing only in the drawing phase.

```kotlin
// INCORRECT (Triggers 60fps recompositions):
val time by animateFloatAsState(...)
Box(modifier = Modifier.drawBehind {
    shader.setFloatUniform("uTime", time) // State read in Composable body!
    drawRect(brush)
})

// CORRECT (Zero recompositions, draw-phase execution only):
val timeState = remember { mutableFloatStateOf(0f) }
Box(modifier = Modifier.drawWithCache {
    val shader = RuntimeShader(SHADER_SRC)
    val brush = ShaderBrush(shader)
    onDrawBehind {
        // Read state inside DrawScope lambda
        shader.setFloatUniform("uTime", timeState.floatValue) 
        drawRect(brush)
    }
})
```

## 3. Shader Caching in `drawWithCache`

Always create shaders and brushes inside `drawWithCache`. This preserves instances across frames, avoiding per-frame memory allocation and compilation lag.

```kotlin
Modifier.drawWithCache {
    // Cache shader creation
    val shader = RuntimeShader(SHADER_SRC)
    val brush = ShaderBrush(shader)
    
    // Set static uniforms
    shader.setFloatUniform("uResolution", size.width, size.height)
    
    onDrawBehind {
        // Apply dynamic uniforms and draw
        shader.setFloatUniform("uTime", elapsedTime)
        drawRect(brush)
    }
}
```

## 4. Advanced: Custom `Modifier.Node` Pattern

For complex UI components (e.g., design systems, backdrop blur containers), implement a custom `Modifier.Node` to cache `GraphicsLayer` and update uniforms without recomposition by utilizing `ObserverModifierNode` and `observeReads`.

```kotlin
class ShaderEffectNode(
    var shaderSrc: String,
    var timeState: () -> Float
) : Modifier.Node(), DrawModifierNode, ObserverModifierNode {

    private var graphicsLayer: GraphicsLayer? = null
    private var shader: RuntimeShader? = null

    override fun onAttach() {
        val context = requireGraphicsContext()
        graphicsLayer = context.createGraphicsLayer()
        shader = RuntimeShader(shaderSrc)
        observeShader()
    }

    override fun onDetach() {
        graphicsLayer?.let { layer ->
            requireGraphicsContext().releaseGraphicsLayer(layer)
            graphicsLayer = null
        }
        shader = null
    }

    override fun onObservedReadsChanged() {
        observeShader()
    }

    private fun observeShader() {
        observeReads {
            val s = shader ?: return@observeReads
            val layer = graphicsLayer ?: return@observeReads
            
            // Set dynamic uniforms
            s.setFloatUniform("uTime", timeState())
            
            // Apply RenderEffect directly to GraphicsLayer
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                layer.renderEffect = RenderEffect.createRuntimeShaderEffect(s, "content").asComposeRenderEffect()
            }
        }
    }

    override fun ContentDrawScope.draw() {
        val layer = graphicsLayer ?: return
        recordLayer(layer) {
            drawContent()
        }
        drawLayer(layer)
    }
}
```

## 5. Compose Multiplatform expect/actual Abstraction

Abstract the shader builder to support multiple platforms (Android AGSL `RuntimeShader` vs Desktop/iOS Skia `RuntimeEffect`).

```kotlin
// commonMain
expect class CommonRuntimeShader(sksl: String) {
    fun setFloatUniform(name: String, value1: Float)
    fun setFloatUniform(name: String, value1: Float, value2: Float)
    fun buildBrush(): Brush
}

// androidMain
actual class CommonRuntimeShader actual constructor(sksl: String) {
    private val shader = RuntimeShader(sksl)
    actual fun setFloatUniform(name: String, value1: Float) { shader.setFloatUniform(name, value1) }
    actual fun setFloatUniform(name: String, value1: Float, value2: Float) { shader.setFloatUniform(name, value1, value2) }
    actual fun buildBrush(): Brush = ShaderBrush(shader)
}

// skiaMain (desktopMain/iosMain)
actual class CommonRuntimeShader actual constructor(sksl: String) {
    private val effect = org.jetbrains.skia.RuntimeEffect.makeForShader(sksl)
    private val builder = org.jetbrains.skia.RuntimeShaderBuilder(effect)
    actual fun setFloatUniform(name: String, value1: Float) { builder.uniform(name, value1) }
    actual fun setFloatUniform(name: String, value1: Float, value2: Float) { builder.uniform(name, value1, value2) }
    actual fun buildBrush(): Brush = ShaderBrush(builder.makeShader())
}
```
