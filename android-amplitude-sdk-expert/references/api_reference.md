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

Three integration paths — pick by SDK type:

| Scenario | Artifact | Approach |
|---|---|---|
| Modern Kotlin SDK (`analytics-android`) | `plugin-session-replay-android` | Plugin (recommended) |
| Legacy/maintenance SDK (`android-sdk`) | `middleware-session-replay-android` | Middleware |
| Third-party analytics (no Amplitude SDK) | `session-replay-android` | Standalone |

---

### 5a. Plugin (Modern Kotlin SDK — recommended)

```kotlin
// build.gradle.kts
implementation("com.amplitude:plugin-session-replay-android:<version>")
implementation("com.amplitude:analytics-android:[1.16.7, 2.0.0]")
```

```kotlin
import com.amplitude.android.Amplitude
import com.amplitude.android.Configuration
import com.amplitude.android.plugins.SessionReplayPlugin

val amplitude = Amplitude(Configuration(apiKey = API_KEY, context = applicationContext))

val sessionReplayPlugin = SessionReplayPlugin(
    sampleRate = 0.5,            // 0.0 (off) to 1.0 (all sessions). Default: 0.0
    maskLevel = "medium",        // "light" | "medium" (default) | "conservative"
    enableRemoteConfig = true,   // pull mask config from Amplitude dashboard. Default: true
)
amplitude.add(sessionReplayPlugin)
```

**`SessionReplayPlugin` params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `sampleRate` | `Double` | `0.0` | Fraction of sessions to capture. `1.0` = all. |
| `maskLevel` | `String` | `"medium"` | Global privacy mask level. |
| `enableRemoteConfig` | `Boolean` | `true` | Override local mask config from dashboard. |
| `recordLogOptions.logCountThreshold` | `Int` | `1000` | Max log entries per session. |
| `recordLogOptions.maxMessageLength` | `Int` | `2000` | Max chars per log message. |

---

### 5b. Middleware (Legacy/Maintenance SDK)

```kotlin
// build.gradle.kts
implementation("com.amplitude:middleware-session-replay-android:<version>")
implementation("com.amplitude:android-sdk:[2.40.1,3.0.0]")
```

```kotlin
import com.amplitude.api.Amplitude
import com.amplitude.api.SessionReplayMiddleware

val amplitude = Amplitude.getInstance()
    .initialize(this, AMPLITUDE_API_KEY)
    .setFlushEventsOnClose(true)

val sessionReplayMiddleware = SessionReplayMiddleware(amplitude, sampleRate = 1.0)
amplitude.addEventMiddleware(sessionReplayMiddleware)

// Always flush before app exits or goes to background
override fun onPause() {
    super.onPause()
    sessionReplayMiddleware.flush()
}
```

---

### 5c. Standalone SDK (Third-party analytics)

```kotlin
// build.gradle.kts
implementation("com.amplitude:session-replay-android:<version>")
```

```kotlin
import com.amplitude.android.sessionreplay.SessionReplay

val sessionReplay = SessionReplay(
    apiKey = "api-key",
    context = applicationContext,
    deviceId = "device-id",
    sessionId = Date().time,
    sampleRate = 1.0,
)

// Sync IDs whenever your analytics SDK changes them
sessionReplay.setSessionId(thirdPartyAnalytics.getSessionId())
sessionReplay.setDeviceId(thirdPartyAnalytics.getDeviceId())

// Always flush before app exits or goes to background
override fun onPause() {
    super.onPause()
    sessionReplay.flush()
}
```

---

### Privacy & Masking Controls

#### Mask Levels
- `light`: Masks passwords, emails, phone numbers, web views, maps.
- `medium`: Masks all editable text inputs, web views, maps. *(default)*
- `conservative`: Masks all text views, web views, maps.

#### Layout XML Attributes (`android:tag`)
```xml
<!-- Unmask a specific input or web view -->
<EditText android:tag="amp-unmask" ... />

<!-- Mask text in a non-input element -->
<TextView android:tag="amp-mask" ... />

<!-- Replace element with solid placeholder -->
<ImageView android:tag="amp-block" ... />
```

#### Jetpack Compose Masking
- **No custom `Modifier`** — SDK does not provide `Modifier.ampMask()` or similar.
- Strategy:
  1. Set global `maskLevel` in `SessionReplayPlugin` (e.g. `"conservative"`).
  2. Override per-component via Amplitude dashboard → Session Replay settings → component selectors.

#### Programmatic Masking (View-level)
```kotlin
import com.amplitude.android.SessionReplay

SessionReplay.mask(myView)    // obscure text as asterisks
SessionReplay.unmask(myView)  // remove masking
SessionReplay.block(myView)   // replace with solid placeholder
```



