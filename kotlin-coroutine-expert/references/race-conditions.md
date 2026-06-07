# Race Conditions

## Decision Matrix

| Pattern | Use When | Cost | Reentrant |
|---|---|---|---|
| `AtomicInteger` / `AtomicReference` | Simple counters, flags, single-value CAS | Lock-free, minimal | N/A |
| `Mutex` | Multi-step state mutation, complex objects | Suspension-based, no thread block | **No** |
| `Semaphore` | Limit concurrent access (rate limiting, DB pool) | Suspension-based | No |
| `Channel` | Producer-consumer, FIFO ordering required | Allocation + serialization | N/A |
| `StateFlow.update{}` | Reactive UI state, single current value | Lock-free CAS | N/A |
| `limitedParallelism(1)` | Serialize access via dispatcher confinement | Context switch | N/A |

## Mutex

```kotlin
val mutex = Mutex()
var counter = 0

// withLock is safe — releases on exception or cancellation
suspend fun increment() = mutex.withLock {
    counter++
}

// DEADLOCK: Mutex is NOT reentrant
suspend fun outer() = mutex.withLock {
    inner() // suspends forever
}
suspend fun inner() = mutex.withLock { /* never reached */ }

// FIX: expose an unlocked version
private suspend fun innerUnsafe() { /* assumes lock held */ }
suspend fun outer() = mutex.withLock { innerUnsafe() }
suspend fun inner() = mutex.withLock { innerUnsafe() }
```

Never use `mutex.lock()` / `mutex.unlock()` directly — always `withLock {}` to guarantee release.

## Semaphore

```kotlin
val semaphore = Semaphore(permits = 4)

// Limit concurrent API calls to 4
suspend fun fetchConcurrentlyBounded(urls: List<String>) = coroutineScope {
    urls.map { url ->
        async {
            semaphore.withPermit {
                httpClient.get(url)
            }
        }
    }.awaitAll()
}
```

## Channel — FIFO Actor Pattern

```kotlin
// Producer-consumer with backpressure
val channel = Channel<Work>(capacity = Channel.BUFFERED)

// Producer
launch {
    items.forEach { channel.send(it) } // suspends if buffer full
    channel.close()
}

// Consumer
launch {
    for (work in channel) { process(work) }
}

// Fixed worker pool
suspend fun workerPool(items: List<Item>, workers: Int = 4) = coroutineScope {
    val jobs = Channel<Item>(workers)
    repeat(workers) {
        launch { for (item in jobs) processItem(item) }
    }
    items.forEach { jobs.send(it) }
    jobs.close()
}
```

Channel capacities:
- `Channel.RENDEZVOUS` (0) — sender suspends until receiver ready
- `Channel.BUFFERED` — platform default buffer (64)
- `Channel.UNLIMITED` — never suspends sender (risk: OOM)
- `Channel.CONFLATED` — only latest value kept

## StateFlow — Atomic update{}

```kotlin
private val _state = MutableStateFlow(0)
val state: StateFlow<Int> = _state.asStateFlow()

// WRONG: read-modify-write race condition
fun incrementBad() {
    _state.value = _state.value + 1
}

// CORRECT: atomic CAS loop
fun increment() {
    _state.update { current -> current + 1 }
}

// CORRECT: complex state update
data class UiState(val count: Int, val loading: Boolean)
private val _uiState = MutableStateFlow(UiState(0, false))

fun startLoading() {
    _uiState.update { it.copy(loading = true) }
}
```

`update {}` uses `compareAndSet` internally — retries if another thread modified the value concurrently.

## @Volatile — Visibility Only

`@Volatile` ensures reads/writes are visible across threads but does NOT guarantee atomicity of compound operations:

```kotlin
@Volatile var initialized = false

// SAFE: simple boolean flag, single write
fun initialize() { initialized = true }
fun isReady() = initialized

// UNSAFE: compound check-then-act is still a race
@Volatile var count = 0
fun incrementBad() { count++ } // read + write = race condition
```

Use `AtomicInteger` / `AtomicBoolean` when you need atomicity, not just visibility.

## Atomic References

```kotlin
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference

val counter = AtomicInteger(0)
counter.incrementAndGet()     // atomic increment
counter.getAndAdd(5)          // atomic add
counter.compareAndSet(0, 1)   // CAS: only sets if current == 0

// AtomicReference for immutable value swaps
data class Config(val timeout: Int, val retries: Int)
val config = AtomicReference(Config(30, 3))

fun updateTimeout(newTimeout: Int) {
    config.updateAndGet { it.copy(timeout = newTimeout) }
}

// compareAndSet pattern
fun tryAcquire(): Boolean {
    return config.compareAndSet(
        config.get(),
        config.get().copy(timeout = 0)
    )
}
```

## Shared Mutable State — Prefer Immutable + Copy

```kotlin
// BAD: mutable shared state
class BadCache {
    private val data = mutableMapOf<String, Any>()
    private val mutex = Mutex()

    suspend fun put(key: String, value: Any) = mutex.withLock {
        data[key] = value
    }
}

// GOOD: immutable snapshot, atomic swap
class GoodCache {
    private val data = AtomicReference(emptyMap<String, Any>())

    fun put(key: String, value: Any) {
        data.updateAndGet { it + (key to value) }
    }

    fun get(key: String) = data.get()[key]
}
```

## conflate() — Drop Stale Emissions

```kotlin
// Only process most recent value, skip intermediates
viewModel.state
    .conflate()
    .collect { render(it) } // never processes stale frames

// Channel.CONFLATED for producer side
val channel = Channel<Update>(Channel.CONFLATED)
// Sending to a full conflated channel replaces, not queues
```

## Common Race Condition Bugs

| Symptom | Cause | Fix |
|---|---|---|
| Counter increments by less than expected | `counter++` without atomics | `AtomicInteger.incrementAndGet()` |
| StateFlow emits stale value under load | `_state.value = _state.value + 1` | `_state.update { it + 1 }` |
| Deadlock in nested Mutex calls | Mutex is non-reentrant | Extract unlocked internal function |
| Cache corruption with concurrent writes | Unsynchronized `MutableMap` | `Mutex.withLock {}` or `ConcurrentHashMap` |
| "Already resumed" exception | `resume()` called twice on continuation | Ensure single resume path; use `resumeWith` guarded by `isActive` |
| Memory leak from fire-and-forget | `GlobalScope.launch` or `SupervisorJob` coroutines without bounds | Use structured scope; bound coroutine count |
| Infinite suspend / deadlock | `runBlocking` inside coroutine, pool exhausted | Never `runBlocking` inside suspend fns |
| Log correlation IDs missing | `ThreadLocal` (MDC) lost on thread hop | Use `MDCContext()` in coroutine context |

## Double-Checked Locking Anti-Pattern

```kotlin
// BROKEN in coroutines — two coroutines can both see instance == null
private var instance: Heavy? = null

suspend fun getInstance(): Heavy {
    if (instance == null) {
        instance = withContext(Dispatchers.Default) { Heavy() } // race here
    }
    return instance!!
}

// CORRECT: Mutex for lazy init
private val mutex = Mutex()
private var instance: Heavy? = null

suspend fun getInstance(): Heavy {
    instance?.let { return it }
    return mutex.withLock {
        instance ?: Heavy().also { instance = it }
    }
}

// SIMPLER: use stdlib lazy with synchronization mode
private val instance by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { Heavy() }
```
