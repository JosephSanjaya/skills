# Store5 Feature Definitions & Niche Constraints

Detailed specifications for Store5 components.

## 1. Fetcher
- **Purpose**: Retrieves data from origin (network/service).
- **Types**:
  - `Fetcher.of { key -> api.get(key) }`: Suspend function, returns single value. Exceptions propagate.
  - `Fetcher.ofResult { key -> FetcherResult }`: Returns structured wrapper. Best for typed errors.
  - `Fetcher.ofFlow { key -> flow { emit(value) } }`: Returns Flow. For streaming/paging responses.
- **Niche/Traps**: Exceptions in `Fetcher.of` are caught by Store and wrapped in `StoreReadResponse.Error.Exception`. Use `Fetcher.ofResult` to bypass exception overhead.

## 2. SourceOfTruth (SoT)
- **Purpose**: Canonical local persistence (Room/SQLDelight).
- **Constraints**:
  - Reader **must** return an observable `Flow`.
  - Reader **must** return `null` if data absent (not empty collection) to trigger Fetcher.
- **Niche**: Direct DB writes bypass Store caching unless SoT reader Flow emits updates. Ensure DB queries are observable.

## 3. Converter
- **Purpose**: Maps types across layers: `NetworkDto` (net) ⇄ `LocalEntity` (db) ⇄ `DomainModel` (UI).
- **Syntax**:
  ```kotlin
  Converter.Builder<Net, Local, Out>()
      .fromNetworkToLocal { net -> net.toLocal() }
      .fromOutputToLocal { out -> out.toLocal() }
      .build()
  ```
- **Niche**: Mandatory for `MutableStore` writes to resolve output domain model back to local DB entity.

## 4. Validator
- **Purpose**: Stale-data check. Evaluates output before serving cache.
- **Syntax**: `Validator.by { output -> output.timestamp + TTL > now() }`
- **Niche**: Validator returning `false` marks data as stale. Store serves stale data first, then runs Fetcher in background (stale-while-revalidate).

## 5. Updater
- **Purpose**: Pushes local database writes to network. Used in `MutableStore`.
- **Niche**: Returns `UpdaterResult`. On fail, schedules retry via conflict resolution. Supports optional `onCompletion` hook for side-effects.

## 6. Bookkeeper
- **Purpose**: Logs fail timestamps for sync retries.
- **Niche**: Keeps map of failed keys. On next read request, checks Bookkeeper; if key failed, runs Updater before Fetcher pulls fresh data.

## 7. MemoryPolicy
- **Purpose**: Memory cache eviction config.
- **Eviction Options**: `expireAfterWrite` vs `expireAfterAccess`.
- **Niche**: Mutually exclusive. Setting both in builder throws `IllegalArgumentException`.

## 8. StoreMultiCache (Experimental)
- **Purpose**: Caches multiple store instances or key ranges.
- **Annotations**: Requires `@ExperimentalStoreApi`.
- **Niche**: Subject to API changes. Use only when single cache instance cannot hold divergent key domains.
