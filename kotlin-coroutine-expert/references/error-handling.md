# Error Handling

## launch vs async — Error Behavior

```kotlin
// launch: exception propagates immediately to parent scope
val scope = CoroutineScope(Job())
scope.launch {
    throw RuntimeException("immediate crash")
    // propagates to scope, cancels all siblings
}

// async: exception deferred until .await()
val deferred = scope.async {
    throw RuntimeException("deferred crash")
}
// no crash yet
deferred.await() // throws here
```

Implication: wrapping `async` in `try-catch` at the launch site does nothing — catch at `await()` instead.

## CoroutineExceptionHandler

Only catches unhandled exceptions in **root** coroutines (top-level `launch` or the scope itself). No-op for nested launches or `async`.

```kotlin
val handler = CoroutineExceptionHandler { _, throwable ->
    logger.error("Unhandled coroutine exception", throwable)
}

// WORKS: top-level launch with handler on scope
val scope = CoroutineScope(SupervisorJob() + handler)
scope.launch {
    throw RuntimeException("caught by handler")
}

// DOESN'T WORK: nested launch — exception propagates to parent, bypasses handler
scope.launch {
    launch(handler) {
        throw RuntimeException("handler ignored here")
    }
}

// DOESN'T WORK: async — exception deferred to .await()
scope.async(handler) {
    throw RuntimeException("handler never fires")
}
```

Handler requires `SupervisorJob` (or `supervisorScope`) as parent to fire — otherwise standard propagation cancels the scope before the handler runs.

## supervisorScope for Independent Failures

```kotlin
// Each child can fail without cancelling siblings
suspend fun loadDashboard(userId: String): Dashboard = supervisorScope {
    val profile = async { profileApi.fetch(userId) }
    val posts = async { postsApi.fetch(userId) }
    val ads = async { adsApi.fetch(userId) }

    Dashboard(
        profile = runCatching { profile.await() }.getOrNull(),
        posts = runCatching { posts.await() }.getOrElse { emptyList() },
        ads = runCatching { ads.await() }.getOrElse { emptyList() },
    )
}
```

## try-catch on suspend Functions

Works exactly like synchronous code:

```kotlin
suspend fun safeFetch(id: String): Result<User> {
    return try {
        val user = api.getUser(id)
        Result.success(user)
    } catch (e: IOException) {
        Result.failure(e)
    }
}
```

## CancellationException — Must Not Swallow

`CancellationException` is the mechanism by which coroutines are cancelled. Catching and swallowing it prevents cancellation from propagating.

```kotlin
// WRONG: swallows cancellation, coroutine becomes uncancellable
suspend fun bad() {
    try {
        delay(Long.MAX_VALUE)
    } catch (e: Exception) {
        logger.error("error", e) // catches CancellationException!
    }
}

// WRONG: same problem
suspend fun bad2() {
    try {
        delay(Long.MAX_VALUE)
    } catch (e: Throwable) {
        logger.error("error", e) // definitely catches CancellationException
    }
}

// CORRECT: rethrow CancellationException
suspend fun good() {
    try {
        delay(Long.MAX_VALUE)
    } catch (e: CancellationException) {
        throw e // must rethrow
    } catch (e: Exception) {
        logger.error("error", e)
    }
}

// CORRECT: catch specific exceptions only
suspend fun good2() {
    try {
        delay(Long.MAX_VALUE)
    } catch (e: IOException) {
        logger.error("io error", e)
    }
}
```

## runCatching + Result

Safe alternative to try-catch blocks, composes well:

```kotlin
suspend fun fetchUser(id: String): Result<User> = runCatching {
    api.getUser(id)
}
// Note: runCatching catches ALL exceptions including CancellationException
// If using runCatching, rethrow CancellationException:

suspend fun fetchUserSafe(id: String): Result<User> {
    return runCatching { api.getUser(id) }
        .onFailure { if (it is CancellationException) throw it }
}

// Chain results
val name = fetchUser("123")
    .map { it.displayName }
    .getOrElse { "Unknown" }
```

## Retry with Exponential Backoff

```kotlin
suspend fun <T> retryWithBackoff(
    maxAttempts: Int = 3,
    initialDelay: Long = 1_000,
    maxDelay: Long = 30_000,
    factor: Double = 2.0,
    block: suspend () -> T,
): T {
    var currentDelay = initialDelay
    repeat(maxAttempts - 1) { attempt ->
        try {
            return block()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            logger.warn("Attempt ${attempt + 1} failed", e)
            delay(currentDelay)
            currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelay)
        }
    }
    return block() // last attempt, let it throw
}

// Usage
val user = retryWithBackoff(maxAttempts = 3) { api.getUser(id) }
```

## Android ViewModel Error Boundary

```kotlin
class UserViewModel(private val repo: UserRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState = _uiState.asStateFlow()

    fun loadUser(id: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            _uiState.value = try {
                UiState.Success(repo.getUser(id))
            } catch (e: CancellationException) {
                throw e // never catch cancellation
            } catch (e: Exception) {
                UiState.Error(e.message ?: "Unknown error")
            }
        }
    }
}
```

## awaitAll vs map { await() }

```kotlin
// BAD: sequential awaiting, poor exception handling
val results = deferreds.map { it.await() }

// GOOD: awaitAll cancels remaining if one fails
val results = deferreds.awaitAll()

// awaitAll with supervisorScope for partial success
supervisorScope {
    val deferreds = items.map { async { process(it) } }
    deferreds.map { runCatching { it.await() } }
}
```
