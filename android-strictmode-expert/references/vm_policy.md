# VmPolicy Diagnostics and Resolutions

VmPolicy monitors memory leaks, lifecycle violations, incorrect context usage, and system security boundaries process-wide.

---

## 1. Leaked Closable Objects & Cursors (`detectLeakedClosableObjects`, `detectLeakedSqlLiteObjects`)

### Mechanism
- File streams, Sockets, and SQLite cursors retain native Linux file descriptors.
- GC sweeps trace unclosed handles and print the allocation stack.
- **Kotlin Bytecode Trap:** AutoCloseable.use (from kotlin-stdlib-jre7/newer JDKs) vs Closeable.use (base stdlib) have minor bytecode differences. Unclosed resources inside complex nested catch blocks may trigger warnings if standard Closeable.use is not resolved properly.

### Code Solutions

#### Kotlin Auto-Close via `use`
```kotlin
fun readData(file: File) {
    FileInputStream(file).use { stream ->
        val data = stream.readBytes()
        // stream is guaranteed closed
    }
}
```

#### SQL Cursor Auto-Close
```kotlin
db.rawQuery("SELECT name FROM users WHERE id = ?", arrayOf(userId)).use { cursor ->
    if (cursor.moveToFirst()) {
        return cursor.getString(0)
    }
}
```

---

## 2. Activity Context & Registration Leaks (`detectActivityLeaks`, `detectLeakedRegistrationObjects`)

### Mechanism
- Static fields/singletons retaining Activity reference, keeping whole view hierarchies in memory.
- BroadcastReceivers and ServiceConnections not unregistered during component destroy.

### Code Solutions

#### Singleton Context Refactoring
```kotlin
class GlobalCache private constructor(context: Context) {
    private val appContext = context.applicationContext // safe from Activity leak

    companion object {
        @Volatile private var instance: GlobalCache? = null
        fun getInstance(context: Context) = instance ?: synchronized(this) {
            instance ?: GlobalCache(context).also { instance = it }
        }
    }
}
```

#### Symmetrical Lifecycle Registration
```kotlin
class MyActivity : AppCompatActivity() {
    private val receiver = MyReceiver()

    override fun onStart() {
        super.onStart()
        registerReceiver(receiver, IntentFilter("ACTION_UPDATE"))
    }

    override fun onStop() {
        super.onStop()
        unregisterReceiver(receiver) // Prevent VM leak
    }
}
```

---

## 3. Incorrect Context Usage (`detectIncorrectContextUse`)

### Mechanism
- Using Application context for window-specific tasks (view inflation, WindowManager lookup).
- Application context is display-agnostic. In multi-window/foldables, it reports wrong layout metrics, corrupting UI.

### Code Solutions

#### Window Context Wrapper
```kotlin
fun showOverlay(context: Context) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        val windowContext = context.createWindowContext(
            context.display!!,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            null
        )
        val inflater = LayoutInflater.from(windowContext)
        // Inflate view legally
    }
}
```

---

## 4. Security: File URI, Cleartext Network & URI Grants

### Mechanism
- `detectFileUriExposure`: Sharing raw `file://` scheme intents across apps. Blocks target without read permissions.
- `detectCleartextNetwork`: Sending unencrypted HTTP/TCP/UDP packets.
- `detectContentUriWithoutPermission`: Sending content:// without explicit read/write flags.
- `detectImplicitUriPermissionGrant` (Targeting Android 18+): Assuming permissions are implicit.

### Code Solutions

#### Secure File Sharing (FileProvider + Flags)
```kotlin
val contentUri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", imageFile)
val intent = Intent(Intent.ACTION_VIEW).apply {
    setDataAndType(contentUri, "image/jpeg")
    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
}
context.startActivity(intent)
```

#### Network Security Configuration (No Cleartext)
```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <base-config cleartextTrafficPermitted="false" />
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">192.168.1.100</domain> <!-- bypass for local testing -->
    </domain-config>
</network-security-config>
```

---

## 5. Intent Routing: Unsafe Intent Launch (`detectUnsafeIntentLaunch`)

### Mechanism
- Android 12+ behavior.
- Three failure pathways:
  1. Launching arbitrary Intent supplied by untrusted external sources.
  2. Cloning intents via `putExtras(Intent)` without sanitizing (nested intent hijacking).
  3. Broad implicit intents broadcast without component specification or package lock.

### Code Solutions

#### Explicit Component Targets & Immutable PendingIntents
```kotlin
// Secure targeting
val secureIntent = Intent(context, SecureReceiver::class.java).apply {
    val validatedExtra = untrustedBundle.getString("key", "")
    putExtra("key", validatedExtra) // Sanitized copy
}

val pendingIntent = PendingIntent.getBroadcast(
    context,
    0,
    secureIntent,
    PendingIntent.FLAG_IMMUTABLE
)
```

---

## 6. Direct Boot & Storage Bounds (`detectCredentialProtectedWhileLocked`, `detectImplicitDirectBoot`)

### Mechanism
- Direct Boot mode (before user enters PIN/pattern).
- Standard Credential Encrypted (CE) storage is locked. Accessing standard SharedPreferences or Database fails/crashes.
- Querying PackageManager without MATCH flags during boot triggers implicit warning.

### Code Solutions

#### Device Protected Storage Context
```kotlin
if (intent.action == Intent.ACTION_LOCKED_BOOT_COMPLETED) {
    val deviceProtectedContext = context.createDeviceProtectedStorageContext()
    val prefs = deviceProtectedContext.getSharedPreferences("boot_prefs", Context.MODE_PRIVATE)
    // Read alarm/scheduling configs safely
}
```

#### Explicit Direct Boot Query Flags
```kotlin
val receivers = context.packageManager.queryBroadcastReceivers(
    Intent("ACTION_BOOT"),
    PackageManager.MATCH_DIRECT_BOOT_AWARE or PackageManager.MATCH_DIRECT_BOOT_UNAWARE
)
```

---

## 7. Blocked Background Activity Launch (`detectBlockedBackgroundActivityLaunch`)

### Mechanism
- Android 15 (API 35) behavior.
- Catches attempts by background applications to launch Activities without explicit foreground context or caller consent.
- Enforces user interface flow consistency.

### Code Solutions
- Require callers to supply opt-in permissions via `ActivityOptions.setPendingIntentBackgroundActivityStartMode()`:
```kotlin
val options = ActivityOptions.makeBasic().apply {
    pendingIntentBackgroundActivityStartMode = ActivityOptions.MODE_BACKGROUND_ACTIVITY_START_ALLOWED
}
```
