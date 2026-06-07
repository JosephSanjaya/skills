---
name: kotlin-coroutine-expert
description: Expert guidance on Kotlin Coroutines — structured concurrency, dispatcher selection, race condition prevention (Mutex/Channel/StateFlow), error propagation, Flow patterns, testing with runTest/TestDispatcher, and production optimization. Use this skill whenever the user writes coroutine code, asks about async Kotlin, needs help with concurrency bugs, race conditions, CoroutineScope lifecycle, suspend functions, Flow operators, or anything related to kotlinx.coroutines.
---

# Kotlin Coroutine Expert

<instructions>
Provide expert guidance on Kotlin Coroutines, structured concurrency, and flow patterns. Check the reference files below for detailed guidelines, best practices, and code examples.
</instructions>

<decision_matrices>

## Dispatcher Selection

| Thread Pool | Dispatcher | Use Case |
|---|---|---|
| Platform CPU cores | `Dispatchers.Default` | CPU-bound tasks (JSON parsing, sorting, computation) |
| platform/virtual (dynamic) | `Dispatchers.IO` | Blocking I/O (network, database, file system) |
| UI thread | `Dispatchers.Main` | UI updates and state observation (Android/Swing) |
| Current thread (suspend-only) | `Dispatchers.Unconfined` | Advanced/tests (avoid in production) |

For limiting I/O concurrency: Use `Dispatchers.IO.limitedParallelism(n)`.
For serialized thread-safe execution: Use `Dispatchers.IO.limitedParallelism(1)` (lighter than a Mutex).

## Concurrency and Race Prevention

| Problem | Best Solution | Reentrant |
|---|---|---|
| Atomic Counter/Flag | `AtomicInteger` / `AtomicBoolean` | N/A |
| Multi-step state mutation | `Mutex.withLock {}` | **No** (deadlocks on nested call) |
| Concurrency rate limit | `Semaphore(n).withPermit {}` | No |
| Reactive UI state | `MutableStateFlow` + `.update {}` | N/A |
| FIFO Queue / Actor | `Channel<T>` | N/A |
| Serial execution | `Dispatchers.IO.limitedParallelism(1)` | N/A |

**Warning**: `@Volatile` guarantees visibility but NOT atomicity of compound operations (e.g. `count++`).

</decision_matrices>

<production_bugs>

## Top 5 Production Bugs

1. **Swallowed CancellationException**: Catching `Exception` or `Throwable` without rethrowing `CancellationException` breaks structured cancellation.
   - *Fix*: Rethrow or catch specific exception types. (See `references/error-handling.md`)
2. **Unbounded Coroutine Explosion**: Using `launch` inside loops on large lists can spawn thousands of coroutines.
   - *Fix*: Chunk the collections or use an actor/channel pattern. (See `references/dispatchers-and-perf.md`)
3. **StateFlow Race Conditions**: Direct assignment like `_state.value = _state.value + 1` causes race conditions under concurrent access.
   - *Fix*: Use `_state.update { it + 1 }`. (See `references/race-conditions.md`)
4. **Mutex Deadlocks**: `Mutex` in Kotlin is non-reentrant. Nested `withLock` calls suspend indefinitely.
   - *Fix*: Extract unlocked helper functions. (See `references/race-conditions.md`)
5. **SupervisorJob in launch**: Passing `SupervisorJob()` as a parameter to a child coroutine builder (e.g. `launch(SupervisorJob())`) severs structured concurrency.
   - *Fix*: Use `supervisorScope {}` instead. (See `references/structured-concurrency.md`)

</production_bugs>

<reference_index>

## Reference Index

- [structured-concurrency.md](references/structured-concurrency.md)
  - Parent-child hierarchy, `GlobalScope` anti-pattern, `SupervisorJob` vs `Job`, `supervisorScope` vs `coroutineScope`, cancellation checkpoints, `withContext`.
  - *Read when*: Scope lifecycle, cancellation failure, supervisor confusion.
- [dispatchers-and-perf.md](references/dispatchers-and-perf.md)
  - Dispatcher rules, `limitedParallelism`, virtual threads, context switching overhead, ThreadLocal/MDC propagation, coroutine explosion, `runBlocking` deadlocks.
  - *Read when*: Concurrency scaling, thread-pool saturation, logging context, performance optimization.
- [race-conditions.md](references/race-conditions.md)
  - Shared mutable state, `Mutex` deadlocks, `Semaphore` limits, `Channel` actor, `StateFlow.update`, atomic references, double-checked locking.
  - *Read when*: Shared state, atomic updates, concurrent access bugs.
- [error-handling.md](references/error-handling.md)
  - `launch` vs `async` error behaviors, `CoroutineExceptionHandler` constraints, `supervisorScope`, `CancellationException` handling, retries with backoff.
  - *Read when*: Crashes in coroutines, error boundaries, custom retry policies.
- [flow-patterns.md](references/flow-patterns.md)
  - Hot vs cold flows, `stateIn`/`shareIn` scopes, `callbackFlow` lifecycle, `channelFlow`, flatMap operators, backpressure.
  - *Read when*: Flows and emissions, wrapping callback APIs, StateFlow vs SharedFlow.
- [testing.md](references/testing.md)
  - `runTest`, `StandardTestDispatcher` vs `UnconfinedTestDispatcher`, virtual time, `MainDispatcherRule`, testing with Turbine, testing cancellation/exceptions.
  - *Read when*: Unit/integration tests, ViewModel testing, flaky async tests.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "cancellation not working" or "leaking coroutines" | `references/structured-concurrency.md` |
| "OutOfMemoryError" or "heavy I/O block" | `references/dispatchers-and-perf.md` |
| "which dispatcher to use" | `references/dispatchers-and-perf.md` |
| "counter wrong under load" or "stale StateFlow" | `references/race-conditions.md` |
| "exception not caught" or "crash in launch" | `references/error-handling.md` |
| "supervisorScope vs coroutineScope" | `references/structured-concurrency.md` & `references/error-handling.md` |
| "wrap callback API" or "StateFlow vs SharedFlow" | `references/flow-patterns.md` |
| "how to test delays" or "flaky coroutine tests" | `references/testing.md` |

</routing_table>

<constraints>
- All coroutine code must use the latest APIs and should handle cancellation exceptions correctly by rethrowing them.
- Developers are required to use appropriate dispatchers (e.g., limit concurrency with limitedParallelism instead of Mutex).
- All unit tests must wrap the test logic in runTest and use either UnconfinedTestDispatcher or StandardTestDispatcher to control virtual time.
- Any output code format must adhere to these structured guidelines only.
</constraints>
