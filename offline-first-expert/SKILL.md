---
name: offline-first-expert
description: "Expert guidance for offline-first KMP and Android architectures using Store5, Room, SQLDelight, Ktor. Always trigger this skill when designing repositories, databases, caching, offline sync, Fetchers, SourceOfTruth, Updaters, Bookkeepers."
---

# Offline-First Expert

Smart guidelines for Store5 + Room/SQLDelight in KMP. Terse syntax. Max token economy.

<instructions>
Use Store5 for KMP-wide caching, sync, conflict logic. Keep architecture clean: Repository hides Store. Use `MutableSharedFlow` with `DROP_OLDEST` to bound memory.
</instructions>

## 1. Quick Decisions

| Case | Pattern | Target |
|---|---|---|
| Read-only caching, no client writes | `Store` | [references/architecture.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/references/architecture.md) |
| Read+write sync, optimistic UI, server conflict resolution | `MutableStore` | [references/architecture.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/references/architecture.md) |
| Server merge / failure tracking | `Updater` + `Bookkeeper` | [references/conflict_resolution.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/references/conflict_resolution.md) |
| Version definition / Maven | Pin `5.1.0-alpha09` | [references/gotchas.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/references/gotchas.md) |
| Store5 features, niche constraints, experimental APIs | Fetcher, Bookkeeper, MultiCache | [references/features.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/references/features.md) |
| Storage selection, memory vs disk, key-value vs SQL DB | Strategy selection | [references/when_to_use.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/references/when_to_use.md) |



## 2. Core Constraints

<boundaries>
- **NEVER** leak `Store`, `StoreReadResponse`, or `StoreWriteRequest` to UI. Wrap in Repository.
- **NEVER** return empty collections from SourceOfTruth reader when absent; return `null` → trigger Fetcher.
- **NEVER** combine `expireAfterWrite` and `expireAfterAccess` in MemoryPolicy builder; throws error.
- **ALWAYS** return observable `Flow` from SourceOfTruth reader. One-shot flow breaks reactivity.
- **ALWAYS** implement TTL validator + 0-20% jitter to prevent thundering herd.
</boundaries>

## 3. Store5 Features & Niche Rules

- **Fetcher**: Origin data source (Network/API).
  - *Niche*: Wrap/prefer `Fetcher.ofResult` to bypass exception overhead. Use `ofFlow` for streaming/paging.
- **SourceOfTruth (SoT)**: Local persistent DB (Room/SQLDelight).
  - *Niche*: Reader MUST return observable Flow. Reader MUST return `null` (not empty collection) on absent data to trigger Fetcher.
- **Converter**: Net DTO ⇄ DB Entity ⇄ Domain Model mapper.
  - *Niche*: Required in `MutableStore` to write domain model back to DB.
- **Validator**: Cache validity gate.
  - *Niche*: Serving stale-while-revalidate first. Add 0-20% TTL jitter to prevent thundering herds.
- **Updater**: Local update publisher to network.
  - *Niche*: Returns `UpdaterResult`. Scheduled for sync retries on fail.
- **Bookkeeper**: Sync error tracker.
  - *Niche*: Tracks failed keys. Blocks fetch if Updater needs retry.
- **MemoryPolicy**: Eviction config.
  - *Niche*: Combining `expireAfterWrite` and `expireAfterAccess` throws exception.
- **StoreMultiCache**: Multi-instance cache (Experimental).
  - *Niche*: Requires `@ExperimentalStoreApi`. Use only for divergent key domains.

## 4. Code Samples

- Repository & StoreBuilder Wiring: [samples/samples.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/samples/samples.md)
- Custom Converter & Updater: [samples/samples.md](file:///Users/jsanjaya/Projects/skills/offline-first-expert/samples/samples.md#converter-and-updater)

<constraints>
Ensure KMP patterns are followed. The repository class must wrap the store, and only the repository should expose data to the UI layer.
</constraints>
