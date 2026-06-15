# Amplitude Kotlin SDK API Reference (Terse)

## 1. Tracking APIs

### Track Event
```kotlin
amplitude.track(
    eventType = "Song Played",
    eventProperties = mapOf("title" to "Happy Birthday", "genre" to "Pop"),
    options = EventOptions().apply { sessionId = 12345L }
)
```
- Custom event payload: `Map<String, Any?>`. No `JSONObject`.
- Main-thread safe. Coroutine-backed background queue.

### Identify User
Update user properties:
```kotlin
val identify = Identify()
    .set("subscription", "premium")
    .setOnce("signup_date", "2026-06-15")
    .add("login_count", 1)
    .unset("temp_tag")
amplitude.identify(identify)
```
- Batching: `identify` events containing only `set` operations batched automatically. Tune: `identifyBatchIntervalMillis`.

### Track Revenue
```kotlin
val revenue = Revenue().apply {
    productId = "com.company.iap.premium"
    price = 9.99
    quantity = 1
    revenueType = "purchase"
    receipt = "iap_receipt_data"
    receiptSignature = "iap_signature"
}
amplitude.revenue(revenue)
```

---

## 2. Autocapture Settings

Configure via `autocapture = setOf(...)` in `Configuration`:
- `AutocaptureOption.SESSIONS`: Tracks `[Amplitude] Start Session` / `End Session`.
- `AutocaptureOption.APP_LIFECYCLES`: Tracks `Application Installed`, `Updated`, `Opened`, `Backgrounded`.
- `AutocaptureOption.SCREEN_VIEWS`: Tracks `Screen Viewed` (Activities/Fragments).
- `AutocaptureOption.DEEP_LINKS`: Tracks `Deep Link Opened`. Call `setIntent(intent)` in `onNewIntent()` for `singleTop` activities.
- `AutocaptureOption.ELEMENT_INTERACTIONS`: Tracks Views & Compose element clicks. Identify Compose elements using `Modifier.testTag("...")`.

---

## 3. Configuration Properties

| Key | Default | Purpose |
|---|---|---|
| `flushQueueSize` | `30` | Event count threshold to trigger upload. |
| `flushIntervalMillis` | `30000` | Time threshold (30s) to trigger upload. |
| `useBatch` | `false` | `true` → `/batch` endpoint (high-volume). `false` → `/httpapi` V2. |
| `serverZone` | `ServerZone.US` | Set `ServerZone.EU` for EU data residency. |
| `optOut` | `false` | `true` → halts all local logging/uploads. |
| `enableCoppaControl` | `false` | `true` → strips ADID, IP, location. |
| `minIdLength` | `5` | Min chars for deviceId/userId. If shorter, ID is stripped. |

---

## 4. Plugin Architecture

Add behaviors to event flow via plugins:
```kotlin
amplitude.add(CustomPlugin())
```
Types:
1. `Before`: Run first, modify events.
2. `Enrichment`: Run second, modify/filter events. Return `null` to drop event.
3. `Destination`: Run last, send to other APIs.

---

## 5. Session Replay

Record and replay user sessions:
1. Add dependency: `implementation("com.amplitude:plugin-session-replay-android:<version>")`
2. Initialize and register plugin:
```kotlin
import com.amplitude.android.plugins.SessionReplayPlugin

val sessionReplayPlugin = SessionReplayPlugin(sampleRate = 1.0)
amplitude.add(sessionReplayPlugin)
```
- Custom sampling: set `sampleRate` (e.g. `0.05` for 5% of sessions).

