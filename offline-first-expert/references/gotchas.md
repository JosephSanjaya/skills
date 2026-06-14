# Store5 Gotchas & Traps

Watch out for these setup mistakes.

## 1. Maven Version Trap
Quickstart `store = "5.1.0"` does NOT resolve. Only `5.1.0-alphaNN` exist on Maven.
Pin verified version:
```kotlin
// libs.versions.toml
store = "5.1.0-alpha09"
```

## 2. Non-Observable SoT Reader
SoT reader must be observable (re-emit on DB change).
- **Bad**: `flow { emit(dao.get(key)) }` (one-shot, no updates).
- **Good**: `dao.observe(key)` (Flow re-emits on DB write).

## 3. Empty List vs Null
SoT reader must return `null` when empty.
- `null` → Store triggers Fetcher.
- Empty list/collection → Store thinks data exists, suppresses Fetcher.

## 4. Cache Policy Exclusivity
MemoryPolicy cannot combine write and access expiry.
- **Bad**: `expireAfterWrite(...)` + `expireAfterAccess(...)` → Throws exception.
- **Good**: Choose one. Store defaults to write.

## 5. Thundering Herd
Validator TTL expiry synchronized across clients → Net crash.
Add 0-20% random jitter to TTL:
```kotlin
val jitter = (0..20).random() / 100.0
val ttl = baseTtl + (baseTtl * jitter)
```
