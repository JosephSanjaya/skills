# Amplitude Android SDK Migration & Identity (Terse)

## 1. SDK Core Differences

| Feature | Modern SDK (`analytics-android`) | Legacy SDK (`android-sdk`) |
|---|---|---|
| Gradle | `com.amplitude:analytics-android:1.+` | `com.amplitude:android-sdk` |
| Package | `com.amplitude.android.*` | `com.amplitude.api.*` |
| Storage | File-based disk queue + SharedPreferences | SQLite DB (`DatabaseHelper`) |
| Network | HTTP V2 (requires 5-char min IDs) | HTTP V1 |
| Extensibility | `Plugin` architecture | `Middleware` runner |

---

## 2. API Mapping

| Legacy (Java) | Modern (Kotlin) |
|---|---|
| `Amplitude.getInstance().initialize(context, KEY)` | `Amplitude(Configuration(apiKey=KEY, context=context))` |
| `logEvent(eventType, properties)` | `track(eventType, properties)` |
| `logRevenueV2(revenue)` | `revenue(revenue)` |
| `uploadEvents()` | `flush()` |
| `addEventMiddleware(middleware)` | `add(plugin)` |

---

## 3. Data Migration & Caveats

- **Auto-migration**: `migrateLegacyData = true` (default). Reads old SQLite DB, converts queued events/identifies to JSON, saves to new file-queue, deletes SQLite DB. Done via `RemnantDataMigration`.
- **Min ID Length constraint**: HTTP V2 rejects userId/deviceId < 5 chars unless `minIdLength` configured smaller. Check ID lengths before initializing or configure `minIdLength` accordingly to prevent dropped IDs.

---

## 4. User Identity & Sessions

- **Session logic**: Automated. Starts on app foreground, expires after 30 mins (`minTimeBetweenSessionsMillis`) of background inactivity.
- **Login/Logout**:
  - Login: `amplitude.setUserId("user_id")`.
  - Logout: `amplitude.reset()`. Nullifies `userId` and generates a new random `deviceId`.
- **Direct-boot crash warning**: SDK uses `SharedPreferences` in credential-encrypted storage. May crash if initialized in a background service before device unlock. Use direct-boot-aware components if initialization in background is mandatory.
