# Flow Patterns

## Cold vs Hot Flows

| Type | Executes | Subscribers | State |
|---|---|---|---|
| `flow {}` (cold) | Per collector | Each gets own execution | None |
| `SharedFlow` (hot) | Continuously | Multiple share one stream | Replay buffer |
| `StateFlow` (hot) | Continuously | Multiple share one stream | Single current value |

```kotlin
// Cold: fresh execution per collect
val coldFlow = flow {
    println("executing") // runs once per collector
    emit(fetchData())
}
coldFlow.collect { } // "executing"
coldFlow.collect { } // "executing" again

// Hot StateFlow: shared, always has value
val stateFlow = MutableStateFlow(0)
stateFlow.value = 42
stateFlow.collect { } // immediately gets 42
```

## flow {} — Cold Flow Builder

```kotlin
fun observeItems(): Flow<Item> = flow {
    while (true) {
        val items = db.getLatestItems()
        emit(items)
        delay(5_000)
    }
}

// flowOn changes the upstream execution context
fun fetchFromNetwork(): Flow<Data> = flow {
    emit(api.fetch()) // runs on IO
}.flowOn(Dispatchers.IO)
```

## StateFlow

Single current value, replay = 1, equality-based emission (only emits on distinct values):

```kotlin
class FeedViewModel : ViewModel() {
    private val _state = MutableStateFlow<FeedState>(FeedState.Loading)
    val state: StateFlow<FeedState> = _state.asStateFlow()

    // CORRECT: atomic update
    private fun setLoaded(items: List<Item>) {
        _state.update { FeedState.Loaded(items) }
    }

    // WRONG: race condition
    private fun setLoadedBad(items: List<Item>) {
        _state.value = FeedState.Loaded(items) // read-modify-write race if concurrent
    }
}

// Android: collect in lifecycle-aware scope
viewLifecycleOwner.lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.state.collect { render(it) }
    }
}
```

## SharedFlow

Multiple subscribers, configurable replay buffer, no equality check:

```kotlin
private val _events = MutableSharedFlow<Event>(
    replay = 0,          // no buffered values for new subscribers
    extraBufferCapacity = 64,
    onBufferOverflow = BufferOverflow.DROP_OLDEST,
)
val events: SharedFlow<Event> = _events.asSharedFlow()

fun emitEvent(event: Event) {
    _events.tryEmit(event) // non-suspending, may drop if buffer full
}

suspend fun emitEventSuspending(event: Event) {
    _events.emit(event) // suspends if buffer full
}
```

Use `replay = 1` to give new subscribers the last value (like StateFlow without equality check).

## stateIn — Android Pattern

Convert cold Flow to hot StateFlow scoped to ViewModel:

```kotlin
class UserViewModel(repo: UserRepository) : ViewModel() {
    val user: StateFlow<User?> = repo.observeUser()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000), // 5s timeout before stopping
            initialValue = null,
        )
}
// WhileSubscribed(5000): upstream active while UI subscribed + 5s grace (survives config change)
// Eagerly: starts immediately, never stops
// Lazily: starts on first subscriber, never stops
```

## shareIn — Cold to Hot

```kotlin
val sharedLocations: SharedFlow<Location> = locationFlow()
    .shareIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(),
        replay = 1,
    )
```

## callbackFlow — Wrapping Callback APIs

```kotlin
fun BluetoothDevice.observeState(): Flow<BtState> = callbackFlow {
    val callback = object : BtStateCallback {
        override fun onStateChanged(state: BtState) {
            trySend(state) // non-suspending; use send() if you need backpressure
        }
        override fun onError(e: Exception) = close(e)
    }

    registerCallback(callback)

    awaitClose { // MANDATORY: called on cancellation or close()
        unregisterCallback(callback)
    }
}.buffer(Channel.CONFLATED) // drop stale BT state updates
```

`awaitClose` is required — omitting it throws `IllegalStateException`.

## channelFlow — Concurrent Emissions

```kotlin
// Emit from multiple coroutines concurrently (not possible with flow {})
fun fetchAll(ids: List<String>): Flow<User> = channelFlow {
    ids.forEach { id ->
        launch { send(api.getUser(id)) } // concurrent launches
    }
}
```

## Key Operators

```kotlin
flow
    .map { transform(it) }
    .filter { it.isValid() }
    .distinctUntilChanged()     // skip if same as previous
    .debounce(300)              // wait 300ms after last emission
    .throttleFirst(1_000)       // max one per second
    .onEach { log(it) }
    .catch { e -> emit(fallback) } // catches upstream errors
    .onCompletion { cause -> cleanup(cause) }
    .collect { render(it) }
```

## flatMapLatest vs flatMapMerge vs flatMapConcat

```kotlin
// flatMapLatest: cancels previous inner flow on new emission (search, UI input)
searchQuery
    .debounce(300)
    .flatMapLatest { query ->
        repo.search(query) // previous search cancelled when new query arrives
    }
    .collect { results -> showResults(results) }

// flatMapMerge: all inner flows run concurrently (parallel fetching)
ids.asFlow()
    .flatMapMerge(concurrency = 4) { id ->
        flow { emit(api.fetch(id)) }
    }
    .collect { result -> process(result) }

// flatMapConcat: sequential, one at a time (ordered processing)
requests.asFlow()
    .flatMapConcat { request ->
        flow { emit(process(request)) }
    }
    .collect { result -> store(result) }
```

## Backpressure

```kotlin
// buffer(): decouple producer and consumer speeds
fastProducer()
    .buffer(capacity = 64)
    .collect { slowConsumer(it) }

// conflate(): skip to latest, drop intermediates
sensorReadings()
    .conflate()
    .collect { updateDisplay(it) } // only processes latest reading

// collectLatest: cancels slow collector for new emissions
searchResults()
    .collectLatest { results ->
        delay(100) // if new results arrive, this is cancelled
        render(results)
    }
```

## flowOn — Upstream Dispatcher

```kotlin
fun heavyFlow(): Flow<Result> = flow {
    emit(heavyComputation()) // runs on Default
}
.flowOn(Dispatchers.Default) // changes upstream only, not downstream collect

// Chaining flowOn affects everything above it
flow { emit(readFile()) }       // runs on IO
    .flowOn(Dispatchers.IO)
    .map { parse(it) }          // runs on Default
    .flowOn(Dispatchers.Default)
    .collect { render(it) }     // runs on caller's context (Main)
```

## onCompletion — Cleanup

```kotlin
fun observeWithCleanup(): Flow<Data> = dataFlow()
    .onCompletion { cause ->
        if (cause != null) {
            logger.error("Flow completed with error", cause)
        }
        closeResources()
    }
```

## suspendCancellableCoroutine — One-Shot Callback Bridge

```kotlin
suspend fun LegacyApi.fetchAsync(): Data = suspendCancellableCoroutine { cont ->
    val listener = object : Callback {
        override fun onSuccess(data: Data) = cont.resume(data)
        override fun onFailure(e: Exception) = cont.resumeWithException(e)
    }
    register(listener)
    cont.invokeOnCancellation { unregister(listener) }
}

// Never use suspendCoroutine (non-cancellable — leaks on scope cancel)
```
