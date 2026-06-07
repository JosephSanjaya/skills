# Operational Best Practices and Phased Rollout

Eradicating StrictMode violations in large or legacy codebases requires a structured approach to maintain developer velocity and prevent production crashes.

---

## 1. Phased Rollout Protocol

Do NOT enable `.detectAll().penaltyDeath()` globally on day one. This halts development due to legacy technical debt (like synchronous SharedPreferences and database init on startup).

```
Rollout Phase
  ├── Phase 1: Catalog & Whitelist ── Log-only (.penaltyLog) + manual testing + whitelist document
  └── Phase 2: Asymmetric Enforcement ─ ThreadPolicy (.penaltyDeath) + VmPolicy (.penaltyLog)
```

### Phase 1: Catalog and Whitelist
1. Enable `detectAll` but restrict penalties to logging or reporting only:
   ```kotlin
   if (BuildConfig.DEBUG) {
       StrictMode.setThreadPolicy(StrictMode.ThreadPolicy.Builder().detectAll().penaltyLog().build())
       StrictMode.setVmPolicy(StrictMode.VmPolicy.Builder().detectAll().penaltyLog().build())
   }
   ```
2. Execute manual test passes across all critical user paths.
3. Record all warnings into a central catalog (e.g. `strictmode.md`).
4. Resolve violations by:
   - Offloading blocking I/O to background Kotlin Coroutines (`withContext(Dispatchers.IO)`).
   - Wrapping unavoidable main-thread operations (like WebView initialization) in localized `allowThreadDiskReads`/`allowThreadDiskWrites` blocks.

### Phase 2: Asymmetric Enforcement
1. **ThreadPolicy:** Upgrade to `.penaltyDeath()`. Thread violations happen synchronously on the exact line of execution. Crashing provides immediate, deterministic feedback to developers.
2. **VmPolicy:** Maintain at `.penaltyLog()` or report to remote dashboards. VM violations (leaked closeables, cursors) are triggered during non-deterministic Garbage Collection sweeps, hours or days after the actual code fault. Crashing during GC destroys debugging velocity because the crash stack trace is disconnected from the current developer activity.

---

## 2. Remote Observability (Telemetry)

For enterprise applications, use `penaltyListener` to report violations to Crashlytics, Sentry, or Datadog.

### Guidelines
- Always route telemetry uploads to a single-thread background executor.
- Never run upload code synchronously inside the listener; it will block the main thread and trigger nested StrictMode violations.

```kotlin
val telemetryExecutor = Executors.newSingleThreadExecutor()

StrictMode.VmPolicy.Builder()
    .detectAll()
    .penaltyListener(telemetryExecutor) { violation ->
        // Safe background reporting
        FirebaseCrashlytics.getInstance().recordException(violation)
    }
    .build()
```

---

## 3. CI/CD Pipeline Integration

Catch performance regressions during pull requests using automated UI tests (Espresso or Compose).

### Implementation
1. Inject a strict ThreadPolicy inside test runner initialization.
2. Capture violations in an atomic reference using a test-specific listener.
3. Assert no violations occurred at the end of the test.

```kotlin
@Test
fun testHomeActivityPerformance() {
    val violationRef = AtomicReference<Throwable?>(null)
    
    InstrumentationRegistry.getInstrumentation().runOnMainSync {
        StrictMode.setThreadPolicy(
            StrictMode.ThreadPolicy.Builder()
                .detectAll()
                .penaltyListener(Executors.newSingleThreadExecutor()) { violation ->
                    violationRef.set(violation)
                }
                .build()
        )
    }

    // Launch UI and perform action
    ActivityScenario.launch(HomeActivity::class.java)
    onView(withId(R.id.btn_load_heavy)).perform(click())

    // Assert build failure on regression
    assertNull("StrictMode violation caught on UI thread", violationRef.get())
}
```

---

## 4. Conflict: LeakCanary False Positives

### Cause
- Android's internal `StrictMode` class maintains static fields (e.g. `sLastVmViolationTime`) to throttle logs.
- These static fields root references to the last tracked Activity, causing LeakCanary to report false-positive memory leaks.

### Resolution
Exclude `StrictMode` internals in the LeakCanary configuration using an ignored reference matcher:

```kotlin
// In test/debug application config
LeakCanary.config = LeakCanary.config.copy(
    referenceMatchers = LeakCanary.config.referenceMatchers + 
        AndroidReferenceMatchers.instance.ignoredMatchers(
            ignoredKeys = setOf("android.os.StrictMode")
        )
)
```
