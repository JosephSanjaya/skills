# Structured Concurrency

## Parent-Child Job Hierarchy

Parent coroutine waits for all children before completing. Each `launch`/`async` creates a new `Job` as child of the scope's job.

```kotlin
val scope = CoroutineScope(Job())
scope.launch {
    launch { delay(1000); println("child 1") }
    launch { delay(2000); println("child 2") }
    // scope completes only after both children finish
}
```

`Job` is the only `CoroutineContext` element NOT inherited by children — the runtime creates a new child `Job` linked to the parent, never reuses the parent's `Job` instance.

## CoroutineScope vs GlobalScope

Never use `GlobalScope`. It launches unmanaged top-level coroutines that:
- Cannot be cancelled deterministically
- Survive application lifecycle boundaries
- Cannot be tested in isolation

```kotlin
// BAD
GlobalScope.launch { doWork() }

// GOOD — tied to a lifecycle
class MyRepository(private val scope: CoroutineScope) {
    fun startWork() = scope.launch { doWork() }
}
```

Android-provided scopes: `viewModelScope`, `lifecycleScope`, `rememberCoroutineScope()`.

Custom scope:
```kotlin
class AppComponent {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    fun onDestroy() = scope.cancel()
}
```

## SupervisorJob vs Regular Job

| Behavior | `Job()` | `SupervisorJob()` |
|---|---|---|
| Child failure → parent cancelled | Yes | No |
| Child failure → siblings cancelled | Yes | No |
| Use case | Dependent tasks (all-or-nothing) | Independent tasks |

```kotlin
// Regular Job: one failure cancels all
val scope = CoroutineScope(Job())
scope.launch {
    launch { throw RuntimeException("fail") } // cancels sibling
    launch { doImportantWork() }              // gets cancelled
}

// SupervisorJob: failures are isolated
val scope = CoroutineScope(SupervisorJob())
scope.launch { throw RuntimeException("fail") } // only this child dies
scope.launch { doImportantWork() }              // continues unaffected
```

`viewModelScope` is internally `CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)`.

## supervisorScope vs coroutineScope

```kotlin
// coroutineScope: any child failure cancels all children + rethrows
suspend fun fetchAll() = coroutineScope {
    val a = async { fetchA() }
    val b = async { fetchB() }
    a.await() + b.await() // if fetchA throws, fetchB is cancelled
}

// supervisorScope: children fail independently, exception must be handled per-child
suspend fun fetchAllIndependent() = supervisorScope {
    val a = async { fetchA() }
    val b = async { fetchB() }
    // must handle each deferred's exception individually
    val resultA = runCatching { a.await() }
    val resultB = runCatching { b.await() }
}
```

**Anti-pattern:** `withContext(SupervisorJob())` — pointless. `withContext` always installs a standard Job, ignoring the supervisor.

**Anti-pattern:** `launch(SupervisorJob())` — breaks structured concurrency. The injected `SupervisorJob` becomes the parent of the outer launch, not a transparent wrapper. Inner launches are still children of a regular Job.

## Cancellation Checkpoints

Coroutines are cooperatively cancelled — they must check for cancellation at suspension points. Pure CPU-bound loops won't respond to cancel:

```kotlin
// BAD: never checks cancellation
suspend fun crunchNumbers() {
    var i = 0L
    while (i < Long.MAX_VALUE) { i++ }
}

// GOOD: yield() suspends, allowing cancellation check
suspend fun crunchNumbers() {
    var i = 0L
    while (i < Long.MAX_VALUE) {
        i++
        if (i % 10_000 == 0L) yield()
    }
}

// GOOD: ensureActive() throws CancellationException if cancelled (no suspension overhead)
suspend fun crunchNumbers() {
    var i = 0L
    while (i < Long.MAX_VALUE) {
        ensureActive()
        i++
    }
}

// GOOD: isActive check for manual cleanup
suspend fun processItems(items: List<Item>) {
    for (item in items) {
        if (!isActive) break
        process(item)
    }
}
```

- `ensureActive()` — throws `CancellationException` if not active; no coroutine suspension
- `yield()` — suspends briefly, enabling cancellation + fairness between coroutines
- `isActive` — boolean check; handle cleanup manually

## withContext for Context Switching

Use `withContext` to switch dispatcher. Never use `launch` + `join` for this:

```kotlin
// BAD: launch + join for context switch
suspend fun loadData(): Data {
    var result: Data? = null
    withContext(Dispatchers.Default) {
        val job = launch(Dispatchers.IO) { result = fetch() }
        job.join()
    }
    return result!!
}

// GOOD
suspend fun loadData(): Data = withContext(Dispatchers.IO) {
    fetch()
}
```

## Scope Creation Patterns

```kotlin
// Android ViewModel
class MyViewModel : ViewModel() {
    fun load() = viewModelScope.launch { /* auto-cancelled on clear() */ }
}

// Android Fragment/Activity
class MyFragment : Fragment() {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        viewLifecycleOwner.lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { render(it) }
            }
        }
    }
}

// Custom scope with cleanup
class DataManager {
    private val job = SupervisorJob()
    private val scope = CoroutineScope(job + Dispatchers.Default)

    fun shutdown() = job.cancel()
}
```

## Job.children Traversal

```kotlin
val scope = CoroutineScope(SupervisorJob())
scope.launch { /* ... */ }
scope.launch { /* ... */ }

// Wait for specific children
scope.coroutineContext[Job]?.children?.forEach { it.join() }

// Cancel all children but keep scope alive
scope.coroutineContext[Job]?.cancelChildren()
```

## The Severed Scope Anti-Pattern

Passing an explicit `Job()` to `withContext` or `launch` severs the parent-child relationship:

```kotlin
// BAD: orphaned coroutine — cancelling parent has no effect
launch(Job()) {
    delay(10_000) // runs even if parent is cancelled
}

// GOOD: child is properly linked
launch {
    delay(10_000)
}
```
