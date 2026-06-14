# Reusable Component Design: Slot APIs, State Hoisting, & API Conventions

## 1. Slot API Pattern
- **Concept**: Composable accepts `@Composable () -> Unit` lambda ("slots"). Component owns structure; caller owns content.
- **Rule**: Put trailing `content: @Composable () -> Unit` last. Scope content (e.g., `ColumnScope.() -> Unit`) to communicate layout rules.
- **Avoid branching slots**: Do not change slot positions in the tree dynamically:
  ```kotlin
  // ❌ BAD: Disposes and recomposes slot content from scratch on state toggle
  if (expanded) Row { content() } else Column { content() }
  ```
- **Fix**: Use `movableContentOf` / `movableContentWithReceiverOf` wrapped in `remember`:
  ```kotlin
  // ✅ GOOD: Preserves state/lifecycle of slot content across hierarchy changes
  val rememberedContent = remember(content) { movableContentOf { content() } }
  if (expanded) Row { rememberedContent() } else Column { rememberedContent() }
  ```

## 2. State Hoisting
- **Stateless vs Stateful**: Expose stateless component (data in, events out) for controllability/previews. Expose stateful wrapper for ease of use.
- **UDF Pattern**: Pass plain `value: T` and `onValueChange: (T) -> Unit`.
- **Do NOT pass VM/State down**:
  - Never pass `ViewModel` or DI instances into reusable UI.
  - Never pass `MutableState<T>` or `State<T>` down. Couples UI, breaks preview, complicates testing.

## 3. Parameter Ordering Conventions
Follow exact ordering:
1. **Required parameters** (no default values; data first, then events).
2. **Optional parameters** (have default values):
   - First optional parameter MUST be `modifier: Modifier = Modifier`.
   - Remaining optional parameters.
3. **Trailing lambda** (if any; usually `content: @Composable () -> Unit`).

Example:
```kotlin
@Composable
fun UserCard(
    username: String,                  // Required data
    onAvatarClick: () -> Unit,         // Required event (onClick, onTextChange, etc.)
    modifier: Modifier = Modifier,     // First optional
    border: BorderStroke? = null,      // Optional visual config
    content: @Composable () -> Unit,   // Trailing slot
)
```

## 4. Naming Conventions
- **Component functions**: PascalCase nouns (`ProfileCard`, not `drawProfileCard`).
- **Factory functions**: Prefix with `remember` (`rememberMyState`).
- **Value-returning composables**: camelCase (`currentDensity()`).
- **Event parameters**: Present-tense `on*` (`onClick`, `onValueChange` - not `onClicked`).
- **CompositionLocals**: Prefix with `Local` (`LocalThemeColor`).
- **Multipreview annotations**: Prefix with `Previews` (`@PreviewsLightDark`).
- **Custom annotation markers**: Suffix with `Composable` (`@MapComposable`).
