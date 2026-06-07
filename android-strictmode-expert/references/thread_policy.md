# ThreadPolicy Diagnostics and Resolutions

ThreadPolicy detects synchronous, blocking operations on the application main (UI) thread.

---

## 1. Disk Reads (`detectDiskReads`)

### Mechanism
- Virtual File System (VFS) inode resolution locks UI thread.
- Standard file streams, SQLite queries, SharedPreferences initialization.
- Android warns: Do not feel forced to remove *all* disk reads (e.g. startup layout/config read); use bypass for necessary ones.

### WebView Exception
- Instantiating `WebView` via `WebViewDatabase.getInstance` opens databases on main thread.
- Triggers inevitable `DiskReadViolation` / `DiskWriteViolation`.
- **Fix:** Wrap WebView construction/setContentView in `allowThreadDiskReads` / `allowThreadDiskWrites`.

### Code Solutions

#### Kotlin: Temporary Scoped Bypass
```kotlin
val oldPolicy = StrictMode.allowThreadDiskReads()
try {
    val sharedPrefs = context.getSharedPreferences("config", Context.MODE_PRIVATE)
    val firstLaunch = sharedPrefs.getBoolean("first_launch", true)
} finally {
    StrictMode.setThreadPolicy(oldPolicy)
}
```

#### Kotlin: Coroutine Offloading
```kotlin
suspend fun loadConfig(): Config = withContext(Dispatchers.IO) {
    // Disk operations run safely on background worker thread
}
```

---

## 2. Disk Writes (`detectDiskWrites`)

### Mechanism
- Physical modification of NAND flash memory blocks UI thread.
- Catastrophic root cause: `SharedPreferences.Editor.apply()`.
  - Appears async, but enqueues finisher Runnable in OS `QueuedWork` queue.
  - On lifecycle transitions (`onPause`, `onStop`, `Service.onDestroy`), UI thread invokes `QueuedWork.waitToFinish()`.
  - Blocks UI thread via `CountDownLatch` until background `fsync()` completes.
  - System bypasses StrictMode checking *inside* `waitToFinish()` (via `StrictMode.allowThreadDiskWrites`), making telemetry stacks point to generic rendering codes or `ActivityThread.handleStopActivity`.
- Room databases or SQLite raw write commands on main thread.

### Code Solutions

#### Kotlin: Complete Migration to Jetpack DataStore
```kotlin
val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_prefs")

class SettingsRepository(private val context: Context) {
    private val PREF_KEY = booleanPreferencesKey("notifications_enabled")

    suspend fun savePreference(enabled: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[PREF_KEY] = enabled
        }
    }
}
```

---

## 3. Network Operations & DNS (`detectNetwork`)

### Mechanism
- DNS queries, TCP handshakes, payload downloads.
- Android 9 (API 28) splits detection:
  - DNS queries (domain resolution) block UI thread → **Violates**.
  - Direct IP resolution (numeric IPs) allowed without triggering policy (for localized local network calls).
- Third-party libraries like `OkHttp` TLS handshake invokes `StrictMode.noteSlowCall` for cryptographic operations.

### Code Solutions

#### Kotlin: Async Network Call with Retrofit/Coroutines
```kotlin
interface ApiService {
    @GET("user/profile")
    suspend fun getProfile(): Profile
}

class UserViewModel(private val api: ApiService) : ViewModel() {
    fun fetchProfile() {
        viewModelScope.launch {
            try {
                val profile = api.getProfile() // OkHttp runs async internally
            } catch (e: Exception) {
                // handle error
            }
        }
    }
}
```

---

## 4. Custom Slow Calls (`detectCustomSlowCalls`)

### Mechanism
- Manual instrumentation of heavy CPU-bound algorithms (bitmap filter, crypto hashing, database mapping) using `StrictMode.noteSlowCall(String)`.
- Alerts downstream consumers if invoked on UI thread.

### Code Solutions

#### Kotlin: Custom noteSlowCall and Dispatcher Offloading
```kotlin
class ImageProcessor {
    suspend fun processBitmap(bitmap: Bitmap): Bitmap = withContext(Dispatchers.Default) {
        StrictMode.noteSlowCall("ImageProcessor.processBitmap")
        // CPU intensive calculations
    }
}
```

---

## 5. Inefficient Unbuffered I/O (`detectUnbufferedIo`)

### Mechanism
- Introduced Android 8.0 (API 26).
- Standard file streams accessed byte-by-byte without buffer.
- Causes excessive User-space / Kernel-space context switches (syscalls).

### Code Solutions

#### Kotlin / Java: BufferedReader / BufferedInputStream Wrappers
```kotlin
fun readFileBuffered(file: File) {
    BufferedReader(FileReader(file)).use { reader ->
        var line: String?
        while (reader.readLine().also { line = it } != null) {
            processLine(line)
        }
    }
}
```

---

## 6. Resource Type Mismatches (`detectResourceMismatches`)

### Mechanism
- Introduced API 23.
- Fetching resource using mismatching type-getter (e.g. integer saved as `<string>` fetched via `Resources.getInteger()`).
- AAPT framework falls back to dynamic parsing (String-to-Int converter), creating heavy layout inflation lag.

### Code Solutions

#### XML and Kotlin Alignment
```xml
<!-- BAD -->
<string name="max_retries">5</string>

<!-- GOOD -->
<integer name="max_retries">5</integer>
```

```kotlin
// Retrieve match
val maxRetries = context.resources.getInteger(R.integer.max_retries)
```
