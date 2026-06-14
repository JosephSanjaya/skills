# Compose Performance Optimization: Strong Skipping & Recomposition

## 1. Strong Skipping Mode (Kotlin 2.0.20+ default)
- **Concept**: Makes restartable composables skippable even with unstable parameters.
- **Equality Checks**:
  - Stable params: structural equality (`equals()`).
  - Unstable params: referential equality (`===`).
- **Lambdas**: Auto-memoized via `remember` unless opting out via `@DontMemoize`.
- **When Stability Annotations still matter**:
  - Strong skipping only skips if the **same instance** arrives.
  - If parent UI rebuilds state via `copy()` (e.g. StateFlow emission) and contains unstable types (e.g., standard `List<T>`, custom unstable class), referential equality (`===`) fails, triggering recomposition.
  - Fix: Annotate nested types as `@Immutable` / `@Stable` or use kotlinx immutable collections.

## 2. Stability Config & Reports
- **Generate reports**:
  ```kotlin
  // build.gradle.kts
  composeCompiler {
      reportsDestination = layout.buildDirectory.dir("compose_reports")
      metricsDestination  = layout.buildDirectory.dir("compose_metrics")
      stabilityConfigurationFile = rootProject.layout.projectDirectory.file("stability_config.conf")
  }
  ```
- **Stability configuration file (`stability_config.conf`)**:
  ```conf
  // Mark external types stable
  kotlin.collections.List
  kotlin.collections.Set
  kotlin.collections.Map
  ```

## 3. Recomposition Scope Minimization
- **derivedStateOf**:
  - Use when inputs change frequently, but outputs change rarely (e.g., scroll position > 0).
  - Pitfall: Do NOT use for cheap calculations where output changes as often as inputs (e.g., `fullName = "$first $last"`).
- **Defer State Reads**:
  - Pass lambdas `param: () -> Dp` instead of resolved value to defer state reads directly to the layout/draw phases. Skips recomposition entirely.
- **snapshotFlow**:
  - Observe Compose state inside coroutines, applying operators (`distinctUntilChanged`, `debounce`).
  ```kotlin
  LaunchedEffect(listState) {
      snapshotFlow { listState.firstVisibleItemIndex }
          .map { it > 0 }.distinctUntilChanged()
          .collect { showButton = it }
  }
  ```
- **produceState**:
  - Collect non-Compose flows/LiveData into Compose State. Auto-disposed.

## 4. Lazy Lists Optimization
- **Keys & ContentTypes**:
  - Always provide `key = { it.id }` (stable, unique).
  - Provide `contentType = { it.type }` to reuse composition slots for similar item types.
- **Image heights**: Give async images fixed sizes or placeholders to prevent scroll jumps and layout re-calculations.
- **LazyListScope callback allocations**:
  - Lambdas inside `LazyListScope` items block are NOT auto-memoized.
  - Fix: Explicitly `remember` item-level callback handlers, keying them by item ID.

## 5. Baseline Profiles
- Avoid interpretation and JIT compilation overhead.
- Ship AOT profiles for top user journeys. Improves startup and rendering by ~30%.
