# Store5 Sync & Conflict Resolution

Server always resolves conflicts. Client defers.

## 1. Conflict Protocol
1. Client does `write(key, value)`.
2. Store writes value to SoT (optimistic update).
3. `Updater` posts write to net.
4. On fail: Bookkeeper records failed sync timestamp.
5. On next read: `tryEagerlyResolveConflicts` checks Bookkeeper.
6. If failed sync exists: re-pushes local SoT value via Updater, then Fetcher pulls server-resolved value.

## 2. Optimistic Update with Rollback
If write fails, rollback local SoT.
```kotlin
suspend fun toggleFavorite(id: Int): Post {
    val prev = store.get(id)
    val next = prev.copy(isFavorite = !prev.isFavorite)
    
    val response = store.write(StoreWriteRequest.of(id, next))
    return when (response) {
        is StoreWriteResponse.Success -> next
        is StoreWriteResponse.Error -> {
            store.write(StoreWriteRequest.of(id, prev)) // Rollback
            prev
        }
    }
}
```

## 3. Client Merge
No first-party client merge API. Resolve on server.
Use Bookkeeper only to log fail timestamps.
