# Koin Scoping & Lifecycle Management

## Scope Hierarchy

```
@Singleton / @Single  (App-wide global scope — survives configuration changes)
    │
    └── @ActivityScope  (Bound to Activity instance — destroyed on finish/rotation)
            │
            ├── @FragmentScope  (Bound to Fragment instance — linked to parent Activity)
            └── @ViewModelScope (ViewModel scope — survives configuration changes, isolated)
                    │
                    └── PROHIBITED: ViewModel cannot resolve Activity/Fragment scoped refs
                        (Resolving these leads to memory leaks — pins Activity on rotation)
```

### Scope Hierarchy Rules:
1. Child scopes **can** access definitions in parent scopes.
2. Parent scopes **cannot** access definitions in child scopes.
3. `@ViewModelScope` is isolated from the transient Activity/Fragment view hierarchy.

## Built-in Scope Annotations

```kotlin
@Single / @Singleton   // Application-wide global singleton
@KoinViewModel         // ViewModel scope, survives configuration changes (rotation)
```

## Custom Scopes (Marker Class Pattern)

Always use a **Marker Class** rather than raw strings for custom annotations. Using string-named scopes in combination with explicit bindings triggers a known bug in early plugin versions where definitions are dropped silently at runtime.

```kotlin
// 1. Declare marker class (needs no body)
class SessionFlowScope

// 2. Register scoped component
@Scope(SessionFlowScope::class)
@Scoped
class SessionCache

// 3. Dependent scoped component
@Scope(SessionFlowScope::class)
@Scoped
class SessionRepository(private val cache: SessionCache)
```

## Custom Scope Lifecycle Management

Custom scopes must be opened and closed manually. Forgetting to call `close()` pins all scoped references in memory, causing resource leaks.

```kotlin
class CustomSessionManager : KoinComponent {
    private var sessionScope: Scope? = null

    fun startSession() {
        // Create or get the scope identified by a session ID
        sessionScope = getKoin().getOrCreateScope<SessionFlowScope>("session_id")
    }

    fun endSession() {
        sessionScope?.close()   // MANDATORY: Closes scope and clears instances
        sessionScope = null
    }
}
```

## Early Compiler Plugin Bugs

### String-Named Scoped Binding Drops
* **Trigger**: Using `name` parameter in `@Scope` along with `binds` array:
  ```kotlin
  // BROKEN: Compiles, but binding is absent at runtime:
  @Scope(name = "my_scope")
  @Scoped(binds = [MyInterface::class])
  class MyImpl : MyInterface
  ```
* **Fix**: Use a marker class instead:
  ```kotlin
  class MyScope
  
  @Scope(MyScope::class)
  @Scoped(binds = [MyInterface::class])
  class MyImpl : MyInterface
  ```

## Scope Access in `KoinComponent`

```kotlin
class MyPresenter : KoinComponent {
    // Injected from parent global scope
    private val repo: UserRepository by inject()

    // Access specific scope manually via identifier
    private val sessionCache: SessionCache
        get() = getKoin().getScope("session_id").get()
}
```

## Android UI Scoping

```kotlin
// Activity-scoped (destroyed when Activity finishes)
@ActivityScope
@Scoped
class ActivityAnalytics

// Fragment-scoped (tied to Fragment lifecycle, parent is Activity)
@FragmentScope
@Scoped
class FragmentPresenter(private val analytics: ActivityAnalytics)  // Can resolve Activity parent deps
```
