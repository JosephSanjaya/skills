# Store5 KMP Architecture

Store5 manages data flow: Network/Memory/Disk.

## 6 Pillars

1. **Fetcher**: Reads from net. Suspend/Flow.
2. **SourceOfTruth (SoT)**: Local disk (Room/SQLDelight). Must return observable `Flow`.
3. **Converter**: Map Network DTO ⇄ Local Entity ⇄ Domain Model.
4. **Validator**: Gates local freshness. Stale data triggers Fetcher.
5. **Updater**: Pushes local updates to net.
6. **Bookkeeper**: Tracks failed syncs.

## Layering

```
UI/Presenter ──[Domain Model]──► Repository (API Boundary)
                                      │
                                      ▼
                             Store5 / MutableStore
                                 /          \
                       [Fetcher]            [SourceOfTruth]
                           │                      │
                           ▼                      ▼
                       Network (Ktor)        Local DB (Room)
```

## Flow Backpressure

SoT reader must bound memory. Pattern:
```kotlin
val mutableSharedFlow = MutableSharedFlow<PostOutput?>(
    replay = 8,
    extraBufferCapacity = 20,
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)
```
Prevents out-of-memory errors on fast data streams.

## Stale-While-Revalidate

Emits cached data first, then network:
```kotlin
store.stream(StoreReadRequest.cached(key, refresh = true))
```
- Emits loading.
- Emits local cached/SoT data (`origin = SourceOfTruth`).
- Triggers fetch, emits fresh data (`origin = Fetcher`).
- UI shows old data instantly, updates when fresh arrives.
