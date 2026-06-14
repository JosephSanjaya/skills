# Modern Compose APIs: Modifier.Node, Style API, & Transitions

## 1. Modifier.Node (Replaces `composed {}`)
- **Why**: `composed {}` is slow, allocated on every recomposition, and not shareable. `Modifier.Node` splits modifiers into stateless `ModifierNodeElement` (allocated once per recomposition, diffed) and stateful `Modifier.Node` (survives recompositions, reused).
- **Structure**:
  - `ModifierNodeElement`: Defines parameters, overrides `create()` and `update()`, implements `equals()` + `hashCode()`.
  - `Modifier.Node`: Implements interfaces for behavior (e.g. `DrawModifierNode`, `LayoutModifierNode`, `SemanticsModifierNode`). Can launch coroutines via `coroutineScope`.
- **Ripples**: `rememberRipple()` is deprecated. Use `ripple()` factory, which can be stored in a top-level constant.

## 2. Style API (Experimental, Compose 1.11 / BOM 2026.04.01)
- **Concept**: Visual style customization parameters (padding, background, border, shape, shadow) grouped inside a `style = { ... }` block or applied via `Modifier.styleable(styleState)`.
- **Why**: Executes styling logic during layout/draw phases, skipping the composition phase entirely. Avoids recomposition.
- **States & Animations**: Built-in state functions (`pressed(Style { ... })`, `hovered(Style { ... })`) wrapping `animate(Style { ... })` transitions.
- **Example**:
  ```kotlin
  val btnStyle = Style {
      background(Color.Blue); shape(RoundedCornerShape(8.dp))
      hovered(Style {
          animate(Style { background(Color.Cyan) })
      })
      pressed(Style {
          animate(Style { scale(0.95f) })
      })
  }
  ```
- **Pitfalls**: Material components do not support `style` params yet. Text-styling via Style API can cause slight regressions (+5.86% time / +9.82% allocations) compared to `CompositionLocalProvider`. Use selectively.

## 3. Shared Element Transitions
- **SharedTransitionLayout**: Root layout providing `SharedTransitionScope`.
- **Modifiers**:
  - `Modifier.sharedElement(...)`: Matched transition for identical elements.
  - `Modifier.sharedBounds(...)`: Container transform for different elements.
- **Keys**: Keys must be stable, unique, and non-null (crucial in recycling lazy layouts).
- **Ordering**: Place `sharedElement` modifier *before* any size modifications to prevent clipping.

## 4. Predictive Back
- **PredictiveBackHandler**: Handle system swipe gestures back-animations.
- **Handling gesture cancellation**:
  - The handler block is a suspend function. Gesture cancellation throws `CancellationException`. You **must** catch it to reset state and prevent crashes or stuck animation states:
  ```kotlin
  PredictiveBackHandler(enabled = isEnabled) { events ->
      try {
          events.collect { event -> progress = event.progress }
          onBackConfirmed()
      } catch (e: CancellationException) {
          progress = 0f // reset on cancel
      }
  }
  ```
