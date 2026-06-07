# Dispatchers and Performance

## Dispatcher Selection

| Dispatcher | Thread Pool | Use For | Never Use For |
|---|---|---|---|
| `Dispatchers.IO` | Dynamic, up to 64 (or `kotlinx.coroutines.io.parallelism` sys prop) | Blocking I/O: network, disk, DB | CPU-bound work (starves IO threads) |
| `Dispatchers.Default` | Fixed at CPU core count | CPU-bound: parsing, sorting, image processing | Blocking calls (deadlocks Default pool) |
| `Dispatchers.Main` | UI thread (Android/Swing) | UI updates, state observation | Any blocking or heavy computation |
| `Dispatchers.Unconfined` | Caller's thread until first suspension | Tests, special cases only | Production code |

```kotlin
// IO: blocking operations
suspend fun fetchUser(id: String) = withContext(Dispatchers.IO) {
    database.query("SELECT * FROM users WHERE id = ?", id)
}

// Default: CPU-bound
suspend fun parseJson(raw: String) = withContext(Dispatchers.Default) {
    Json.decodeFromString<Response>(raw)
}

// Main: UI only
suspend fun showResult(result: String) = withContext(Dispatchers.Main) {
    textView.text = result
}
```

## limitedParallelism

Carve a sub-pool from `Dispatchers.IO` without creating new threads. Useful for serialized access or bounded concurrency:

```kotlin
// Serialized access — single coroutine at a time, no Mutex needed
val serialDispatcher = Dispatchers.IO.limitedParallelism(1)

// Rate-limited — max 4 concurrent DB operations
val dbDispatcher = Dispatchers.IO.limitedParallelism(4)

class CacheManager {
    private val cacheDispatcher = Dispatchers.IO.limitedParallelism(1)

    suspend fun write(key: String, value: ByteArray) = withContext(cacheDispatcher) {
        cache.put(key, value) // safe, serialized
    }
}
```

`limitedParallelism` on `Default` creates a view that limits concurrency within the Default pool — does not create extra threads.

## Custom Thread Pools

```kotlin
// Single dedicated thread (use sparingly)
val singleThread = newSingleThreadContext("db-writer")

// Fixed thread pool (for legacy blocking libraries)
val legacyPool = newFixedThreadPoolContext(4, "legacy-pool")

// ALWAYS close when done
singleThread.close()
legacyPool.close()

// Prefer Executors API for interop
val executor = Executors.newFixedThreadPool(4)
val dispatcher = executor.asCoroutineDispatcher()
// executor.shutdown() when done
```

## Context-Switching Cost

Each `withContext` call crosses a dispatcher boundary. Redundant switches in hot paths cause measurable overhead (~30% degradation in high-throughput services).

```kotlin
// BAD: 3 context switches for one operation
suspend fun getUserProfile(userId: String) = withContext(Dispatchers.IO) {
    val raw = db.fetch(userId)
    val parsed = withContext(Dispatchers.Default) { parseProfile(raw) }
    withContext(Dispatchers.IO) { cache.write(parsed) }
    parsed
}

// GOOD: batch work, minimize boundaries
suspend fun getUserProfile(userId: String): Profile {
    val raw = withContext(Dispatchers.IO) { db.fetch(userId) }
    val parsed = withContext(Dispatchers.Default) { parseProfile(raw) }
    withContext(Dispatchers.IO) { cache.write(parsed) }
    return parsed
}

// BETTER: if parse is fast, skip the Default switch
suspend fun getUserProfile(userId: String): Profile = withContext(Dispatchers.IO) {
    val raw = db.fetch(userId)
    val parsed = parseProfile(raw) // fast enough to stay on IO
    cache.write(parsed)
    parsed
}
```

Rule: only switch dispatcher when the work type genuinely changes (blocking → CPU or CPU → UI).

## Thread-Local Propagation

`ThreadLocal` values are lost when coroutines hop threads. Use `ThreadContextElement` to propagate:

```kotlin
class MyLocalElement(private val value: String) : ThreadContextElement<String?> {
    companion object Key : CoroutineContext.Key<MyLocalElement>
    override val key = Key

    override fun updateThreadContext(context: CoroutineContext): String? {
        val old = myThreadLocal.get()
        myThreadLocal.set(value)
        return old
    }

    override fun restoreThreadContext(context: CoroutineContext, oldState: String?) {
        myThreadLocal.set(oldState)
    }
}

// Usage
launch(MyLocalElement("request-123")) {
    delay(100) // thread hop
    println(myThreadLocal.get()) // still "request-123"
}
```

For SLF4J MDC specifically, use `kotlinx-coroutines-slf4j`:
```kotlin
launch(Dispatchers.IO + MDCContext()) {
    logger.info("traceId preserved across thread hops")
}
```

## Unbounded Coroutine Anti-Pattern

The Agoda incident: 3 million suspended coroutines from fire-and-forget launches caused 12 GB memory usage and GC lockup.

```kotlin
// BAD: unbounded — one coroutine per item, no backpressure
suspend fun processOrders(orders: List<Order>) {
    orders.forEach { order ->
        launch(Dispatchers.IO) { processOrder(order) }
    }
}

// GOOD: bounded with chunked processing
suspend fun processOrders(orders: List<Order>) = coroutineScope {
    orders.chunked(100).forEach { chunk ->
        chunk.map { async(Dispatchers.IO) { processOrder(it) } }.awaitAll()
    }
}

// GOOD: actor pattern with fixed worker pool (backpressure built-in)
suspend fun processLargeDataSet(items: List<DataItem>, concurrency: Int = 10) = coroutineScope {
    val channel = Channel<DataItem>(concurrency)
    repeat(concurrency) {
        launch {
            for (item in channel) {
                processItem(item)
            }
        }
    }
    items.forEach { channel.send(it) }
    channel.close()
}
```

## Virtual Threads as Coroutine Dispatcher (JVM 21+)

Eliminates blocking-on-IO-dispatcher risk for legacy synchronous libraries:

```kotlin
val virtualThreadDispatcher = Executors.newVirtualThreadPerTaskExecutor()
    .asCoroutineDispatcher()

suspend fun callLegacyBlocking() = withContext(virtualThreadDispatcher) {
    legacySyncClient.makeBlockingCall() // safe — VT parks, not platform thread
}
```

## runBlocking Deadlock

`Dispatchers.Default` pool size = CPU core count. If all threads are blocked by `runBlocking`, the pool deadlocks. Timeouts cannot help — the scheduler itself is frozen.

```kotlin
// DANGEROUS in a coroutine context
suspend fun bad() = withContext(Dispatchers.Default) {
    runBlocking { // blocks a Default thread
        delay(1000)
    }
}
```

Never call `runBlocking` inside a `suspend` function or inside a coroutine body.
