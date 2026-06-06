# Jetpack Compose Memory Management Reference

## 1. Flow Collection: collectAsStateWithLifecycle()
- **Issue**: Standard `collectAsState()` keeps flow collection active even when the app is in the background, wasting CPU and keeping references/resources active.
- **Solution**: Use `collectAsStateWithLifecycle()` from `androidx.lifecycle:lifecycle-runtime-compose` dependency.
  - Automatically cancels flow collection when the lifecycle falls below `STARTED` (e.g. app in background).
  - Resumes collection when it returns to `STARTED`.
  ```kotlin
  // In Gradle
  implementation("androidx.lifecycle:lifecycle-runtime-compose:2.10.0")

  // In Composable
  val uiState by viewModel.uiState.collectAsStateWithLifecycle()
  ```

---

## 2. Lambda Closures & remember Blocks
- **Issue**: Closures in Compose capture and retain references. If a lambda inside `remember` registers a callback to an external static/singleton or long-lived system service without unregistering, it leaks the enclosing context (Activity, Views).
- **Solution**: Use `DisposableEffect` to manage registration/unregistration. Symmetrically call unregister in the `onDispose` block.

---

## 3. ViewModel Retention of Composables
- **Issue**: ViewModels survive configuration changes (rotations). Storing Composable functions (`@Composable () -> Unit`) or layout-bound objects in a ViewModel holds references to the composition hierarchy, causing massive leaks.
- **Solution**: Restrict ViewModel properties to data states and flow flows. Composables should be stateless observers of the ViewModel's state.

---

## 4. Effect Handlers & State Optimization
### 4.1. DisposableEffect Teardown
Symmetrically unregisters listeners when the Composable leaves composition:
```kotlin
DisposableEffect(systemService) {
    val listener = SystemListener { /* ... */ }
    systemService.register(listener)
    onDispose {
        systemService.unregister(listener)
    }
}
```

### 4.2. rememberUpdatedState Callback Guarding
If a listener callback changes, `DisposableEffect` normally has to restart. To prevent continuous registration churn while using the latest callback code, wrap it in `rememberUpdatedState`:
```kotlin
val currentCallback by rememberUpdatedState(onCallback)
DisposableEffect(service) {
    val listener = Listener { currentCallback() } // uses latest callback reference
    service.register(listener)
    onDispose { service.unregister(listener) }
}
```

### 4.3. derivedStateOf GC Mitigation
- **Issue**: States dependent on rapidly changing values (like scroll offset) allocate new state instances repeatedly on every single offset change, causing high GC allocation pressure and jank.
- **Solution**: Wrap calculations in `derivedStateOf` to only trigger recomposition and allocations when the boolean outcome of the threshold changes:
  ```kotlin
  val showScrollToTop by remember {
      derivedStateOf { listState.firstVisibleItemIndex > 0 }
  }
  ```

### 4.4. LaunchedEffect Coroutine Safety
- **Issue**: Lauching a coroutine inside Composable code without binding to lifecycle runs indefinitely and can leak if the UI is dismissed.
- **Solution**: Use `LaunchedEffect` which cancels its coroutine context automatically when the Composable leaves composition.
