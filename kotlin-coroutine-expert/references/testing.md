# Coroutine Testing

## Dependencies

```kotlin
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.11.0")
testImplementation("app.cash.turbine:turbine:1.2.0") // Flow testing
```

## runTest Basics

Creates a `TestScope` with virtual time. Auto-advances past all delays at end of block.

```kotlin
@Test
fun `loads user on init`() = runTest {
    coEvery { repo.getUser("123") } returns user
    val sut = UserViewModel(repo)
    assertThat(sut.uiState.value).isEqualTo(UiState.Success(user))
}
```

## StandardTestDispatcher vs UnconfinedTestDispatcher

| Dispatcher | Execution | Use For |
|---|---|---|
| `StandardTestDispatcher` (default) | Queued; must manually advance | Asserting intermediate states (Loading → Success) |
| `UnconfinedTestDispatcher` | Eager; runs on current thread immediately | Simple suspend fns, Flow collection, when intermediate states don't matter |

```kotlin
// StandardTestDispatcher: control execution order
@Test
fun `shows loading then success`() = runTest {
    val dispatcher = StandardTestDispatcher(testScheduler)
    val sut = UserViewModel(repo, dispatcher)

    sut.loadUser("123")
    assertThat(sut.uiState.value).isEqualTo(UiState.Loading) // not yet run

    advanceUntilIdle()
    assertThat(sut.uiState.value).isEqualTo(UiState.Success(user))
}

// UnconfinedTestDispatcher: eager collection
@Test
fun `collects flow eagerly`() = runTest(UnconfinedTestDispatcher()) {
    val sut = UserViewModel(repo)
    // StateFlow immediately updated, no advanceUntilIdle needed
    assertThat(sut.uiState.value).isEqualTo(UiState.Success(user))
}
```

## Virtual Time Control

```kotlin
// advanceUntilIdle(): runs all queued coroutines, skips all delays
// advanceTimeBy(ms): advances clock by amount, runs coroutines scheduled before that point
// runCurrent(): runs only currently queued coroutines (no time advance)
// currentTime: read virtual clock value

@Test
fun `retries with exponential backoff`() = runTest {
    coEvery { api.fetch() } throws IOException() andThen IOException() andThen response

    sut.fetchWithRetry()

    advanceTimeBy(1_000) // first retry delay
    coVerify(exactly = 2) { api.fetch() }

    advanceTimeBy(2_000) // second retry delay
    coVerify(exactly = 3) { api.fetch() }

    advanceUntilIdle()
    assertThat(sut.state.value).isEqualTo(UiState.Success)
}

@Test
fun `debounce fires after 300ms`() = runTest {
    sut.onSearchQuery("ko")
    advanceTimeBy(299)
    coVerify(exactly = 0) { repo.search(any()) }

    advanceTimeBy(1)
    coVerify(exactly = 1) { repo.search("ko") }
}
```

## MainDispatcherRule

Required for ViewModels using `Dispatchers.Main` (not available on JVM):

```kotlin
class MainDispatcherRule(
    val testDispatcher: TestDispatcher = UnconfinedTestDispatcher(),
) : TestWatcher() {
    override fun starting(description: Description) = Dispatchers.setMain(testDispatcher)
    override fun finished(description: Description) = Dispatchers.resetMain()
}

@get:Rule val mainDispatcherRule = MainDispatcherRule()
```

## Inject Dispatchers for Testability

```kotlin
// Production class
class UserRepository(
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {
    suspend fun loadUser(id: String) = withContext(ioDispatcher) {
        db.query(id)
    }
}

// Test
@Test
fun `loads user from db`() = runTest {
    val repo = UserRepository(ioDispatcher = StandardTestDispatcher(testScheduler))
    val result = repo.loadUser("123")
    assertThat(result).isEqualTo(user)
}
```

## ViewModel Testing

```kotlin
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class UserViewModelTest {
    @get:Rule val mainDispatcherRule = MainDispatcherRule()

    private val repo = mockk<UserRepository>()
    private val sut = UserViewModel(repo, StandardTestDispatcher())

    @Test
    fun `shows loading state before data arrives`() = runTest {
        coEvery { repo.getUser(any()) } coAnswers {
            delay(100)
            user
        }

        sut.loadUser("123")
        assertThat(sut.uiState.value).isEqualTo(UiState.Loading)

        advanceUntilIdle()
        assertThat(sut.uiState.value).isEqualTo(UiState.Success(user))
    }
}
```

## Flow Testing with Turbine

```kotlin
@Test
fun `emits loading then success`() = runTest {
    coEvery { repo.getUser("123") } returns user

    viewModel.uiState.test {
        assertThat(awaitItem()).isEqualTo(UiState.Loading)
        assertThat(awaitItem()).isEqualTo(UiState.Success(user))
        cancelAndIgnoreRemainingEvents()
    }
}

@Test
fun `emits error on failure`() = runTest {
    coEvery { repo.getUser(any()) } throws IOException("network error")

    viewModel.uiState.test {
        awaitItem() // Loading
        val error = awaitItem() as UiState.Error
        assertThat(error.message).contains("network error")
        cancelAndIgnoreRemainingEvents()
    }
}
```

## Testing Race Conditions

```kotlin
@Test
fun `concurrent increments are safe`() = runTest {
    val counter = AtomicInteger(0)
    val jobs = List(100) {
        launch { counter.incrementAndGet() }
    }
    advanceUntilIdle()
    assertThat(counter.get()).isEqualTo(100)
}

@Test
fun `mutex prevents concurrent writes`() = runTest {
    val sut = SharedResource()
    List(50) { launch { sut.increment() } }
    advanceUntilIdle()
    assertThat(sut.count).isEqualTo(50)
}
```

## Testing Cancellation

```kotlin
@Test
fun `cancellation does not show error`() = runTest {
    val job = launch { sut.loadUser("123") }
    job.cancel()
    advanceUntilIdle()
    assertThat(sut.uiState.value).isNotInstanceOf(UiState.Error::class.java)
}

@Test
fun `cleanup runs on cancellation`() = runTest {
    var cleanupCalled = false
    val flow = flow {
        try {
            emit(1)
            delay(Long.MAX_VALUE)
        } finally {
            cleanupCalled = true
        }
    }

    val job = launch { flow.collect { } }
    advanceUntilIdle()
    job.cancel()
    advanceUntilIdle()

    assertThat(cleanupCalled).isTrue()
}
```

## Testing Exception Propagation

```kotlin
@Test
fun `shows error state when fetch throws`() = runTest {
    coEvery { repo.getUser(any()) } throws NetworkException("timeout")

    sut.loadUser("123")
    advanceUntilIdle()

    assertThat(sut.uiState.value).isInstanceOf(UiState.Error::class.java)
}

@Test
fun `CoroutineExceptionHandler captures unhandled exception`() = runTest {
    var caught: Throwable? = null
    val handler = CoroutineExceptionHandler { _, e -> caught = e }
    val scope = CoroutineScope(SupervisorJob() + handler)

    scope.launch { throw RuntimeException("test") }
    advanceUntilIdle()

    assertThat(caught).isInstanceOf(RuntimeException::class.java)
}
```

## Testing Concurrent Parallel Fetches

```kotlin
@Test
fun `fetches concurrently, not sequentially`() = runTest {
    coEvery { userApi.get("123") } coAnswers { delay(100); user }
    coEvery { postApi.getForUser("123") } coAnswers { delay(150); posts }

    val startTime = currentTime
    val result = sut.loadDashboard("123")
    val elapsed = currentTime - startTime

    assertThat(elapsed).isLessThan(200) // parallel: ~150ms not 250ms
    assertThat(result.user).isEqualTo(user)
    assertThat(result.posts).isEqualTo(posts)
}
```

## Testing StateFlow with stateIn

```kotlin
@Test
fun `stateIn emits initial then updates`() = runTest {
    val repo = FakeUserRepo()
    val vm = UserViewModel(repo)

    // Use backgroundScope for flows that don't complete
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        vm.user.collect { }
    }

    assertThat(vm.user.value).isEqualTo(null) // initial
    repo.emitUser(user)
    assertThat(vm.user.value).isEqualTo(user)
}
```

## Common Test Pitfalls

| Problem | Cause | Fix |
|---|---|---|
| Test hangs forever | Collecting infinite Flow without `backgroundScope` or `turbine` | Use `turbine .test {}` or `backgroundScope.launch` |
| `advanceUntilIdle()` does nothing | Dispatcher not using `testScheduler` | Inject `StandardTestDispatcher(testScheduler)` |
| Race in test — non-deterministic | Real `Dispatchers.IO` in production code | Inject dispatcher, use `StandardTestDispatcher` in tests |
| `Dispatchers.Main` not available | Missing `MainDispatcherRule` | Add `@get:Rule val mainRule = MainDispatcherRule()` |
| Test passes when it shouldn't | `UnconfinedTestDispatcher` skips Loading state | Use `StandardTestDispatcher` for intermediate state assertions |
