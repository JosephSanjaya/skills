---
name: android-strictmode-expert
description: >
  Expert guidance for Android StrictMode integration, diagnostics, and optimization. Covers ThreadPolicy (disk I/O, network, custom slow calls, unbuffered IO, resource mismatches) and VmPolicy (memory leaks, incorrect context, intent routing, secure BAL in Android 15/API 35). Directs whitelisting and custom penalties via StrictPro. Triggers: "StrictMode", "ThreadPolicy", "VmPolicy", "detectDiskReads", "detectDiskWrites", "detectNetwork", "detectCustomSlowCalls", "detectUnbufferedIo", "detectResourceMismatches", "detectActivityLeaks", "detectUntaggedSockets", "detectCleartextNetwork", "detectNonSdkApiUsage", "detectContentUriWithoutPermission", "detectImplicitDirectBoot", "detectIncorrectContextUse", "detectLeakedClosableObjects", "detectLeakedRegistrationObjects", "detectUnsafeIntentLaunch", "detectFileUriExposure", "detectCredentialProtectedWhileLocked", "detectLeakedSqlLiteObjects", "detectBlockedBackgroundActivityLaunch", "allowThreadDiskReads", "allowThreadDiskWrites", "StrictPro".
---

# Android StrictMode Expert

## 1. Quick Decision Tree

```
What is target issue?
├── Block UI thread (dropped frames, ANR) ── ThreadPolicy (read references/thread_policy.md)
│   ├── SharedPreferences waitToFinish / commit ── Migrate to Jetpack DataStore
│   ├── WebView database initialization ───────── Wrap allowThreadDiskWrites / allowThreadDiskReads
│   └── DNS query or network TLS handshake ────── Dispatch background threads (Retrofit/Coroutines)
├── Memory/Security/Intent violations ────────── VmPolicy (read references/vm_policy.md)
│   ├── Unclosed SQLite Cursor or Closeable ────── Wrap in kotlin-stdlib .use block
│   ├── Application context used for layout ────── Use Activity / createWindowContext API
│   ├── Sharing raw file:// URI ───────────────── Use FileProvider + FLAG_GRANT_READ_URI_PERMISSION
│   └── Android 15 background activity blocked ── Use ActivityOptions background start modes
└── Whitelist / Custom penalties needed ───────── StrictPro library (read references/strictpro.md)
```

<instructions>
Use strict coding paradigms. Restrict main-thread blocking operations. Route all background operations through Kotlin Coroutines (Dispatchers.IO for I/O, Dispatchers.Default for CPU-bound tasks). Wrap unavoidable main thread I/O in allowThreadDiskReads / allowThreadDiskWrites.
</instructions>

---

## 2. Core Policies Reference Index

Read these detailed guides for code-level diagnostics and resolutions:

*   [thread_policy.md](file:///Users/jsanjaya/.gemini/config/skills/android-strictmode-expert/references/thread_policy.md): Direct analysis of thread-level diagnostics (disk reads, disk writes, unbuffered I/O, network sockets, custom slow calls, resource mismatches).
*   [vm_policy.md](file:///Users/jsanjaya/.gemini/config/skills/android-strictmode-expert/references/vm_policy.md): Direct analysis of VM-level diagnostics (closable resource leaks, activity context leaks, BroadcastReceiver/ServiceConnection leaks, incorrect display context, File URI exposure, unsafe intent launches, Direct Boot storage bounds, blocked background activity launches).
*   [strictpro.md](file:///Users/jsanjaya/.gemini/config/skills/android-strictmode-expert/references/strictpro.md): Structure of the StrictPro library, whitelisting stack signatures, and customizing penalty executors.
*   [best_practices.md](file:///Users/jsanjaya/.gemini/config/skills/android-strictmode-expert/references/best_practices.md): Setup templates, phased rollout protocol, remote observability telemetry, LeakCanary conflicts, and CI/CD automated test verification.

---

## 3. Essential Config Templates

### Scoped Thread I/O Bypass
```kotlin
val oldPolicy = StrictMode.allowThreadDiskReads()
try {
    // Unavoidable sub-millisecond configuration reads on startup
} finally {
    StrictMode.setThreadPolicy(oldPolicy)
}
```

### StrictPro Setup DSL
```kotlin
class MainApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        if (BuildConfig.DEBUG) {
            StrictPro.listenActivities(this)
            StrictPro.setThreadPolicy(
                StrictPro.ThreadPolicy.Builder()
                    .detectAll()
                    .penaltyLog()
                    .penaltyDeath() // Crash on UI thread I/O
                    .setWhiteList {
                        contains("android.webkit.WebViewDatabase", null) // ignore WebView database load
                    }
                    .build()
            )
            StrictPro.setVmPolicy(
                StrictPro.VmPolicy.Builder()
                    .detectAll()
                    .penaltyLog() // Log only (prevent GC non-deterministic crashes)
                    .build()
            )
        }
    }
}
```

---

## 4. Operational Scanner Script

Automated Python script [scan_strictmode_violations.py](file:///Users/jsanjaya/.gemini/config/skills/android-strictmode-expert/scripts/scan_strictmode_violations.py) scans directories recursively to flag common violations (e.g. `.commit()`, unbuffered I/O, `file://` intents, raw socket requests).

Run audit check:
```bash
python3 /Users/jsanjaya/.gemini/config/skills/android-strictmode-expert/scripts/scan_strictmode_violations.py <path_to_android_project>
```

---

## 5. Key Safeguards

> [!IMPORTANT]
> **Phased Rollout Rule:**
> - Phase 1: Enable log-only `.penaltyLog()` process-wide to record all issues in `strictmode.md`.
> - Phase 2: Upgrade ThreadPolicy to `.penaltyDeath()` for deterministic developer loop. Keep VmPolicy at `.penaltyLog()` to avoid non-deterministic process termination during GC sweeps.

> [!WARNING]
> **LeakCanary False Positives:**
> - Android `StrictMode` static fields retain the last seen Activity. Exclude `android.os.StrictMode` in LeakCanary `referenceMatchers` configuration to prevent false memory leak reports.

<constraints>
MUST maintain compatibility with targetSdk 35 (Android 15) guidelines.
MUST avoid cleartext network payloads.
MUST expose files strictly via FileProvider content:// URIs.
Format all Android code output as clean Kotlin or Java with explicit lifecycle and dispatcher mappings.
</constraints>
