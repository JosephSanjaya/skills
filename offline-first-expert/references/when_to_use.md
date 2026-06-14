# Offline-First: When to Use & Storage Selection

Guidelines for architecture selection.

## 1. When to Use Offline-First
- **Core Continuity**: App must work offline (field work, transit, weak cell zones).
- **Optimistic UI**: User inputs must echo instantly. Background sync handles latency.
- **Read Heavy**: Repeat reads of identical keys. Cache stops redundant net calls.

## 2. When NOT to Use
- **Real-Time Only**: Stock prices, live sports, bidding. Stale data violates correctness.
- **Thin Admin Tools**: Internal CRUD on corporate Wi-Fi. No continuity value.
- **One-Shot Actions**: Payments, OTP, OAuth. Inherently blocking, network-required.

## 3. Memory Cache vs Local Storage (Disk)
- **Memory Cache Sufficient**:
  - Feeds refreshed on app start (e.g. social timeline).
  - Short-lived session states/tokens.
  - No need to survive process death/device restarts.
- **Local Storage Required**:
  - Drafts, offline articles, user settings.
  - Data must survive app closure, reboot, or OS process reclamation.

## 4. Key-Value vs Complex Relational DB
- **Key-Value (SharedPreferences, DataStore, basic cache)**:
  - Isolated configurations, user preferences.
  - Flat JSON blobs indexed by single key.
  - No querying, filtering, sorting, or entity relationships.
- **Complex DB (Room, SQLDelight)**:
  - Structured entities with foreign keys (e.g., User ⇄ Posts ⇄ Comments).
  - Complex filtering, indexing, search queries.
  - Large data collections requiring pagination (Paging3).
