# StrictPro Library Architecture and Custom Penalties

StrictPro is a wrapper designed to resolve Android's built-in StrictMode limitations:
- **No visual feedback:** Adds dialog/flash screen notifications.
- **Uncontrolled crashes:** Restricts `penaltyDeath` by selective whitelist matching.
- **Transitive bloat in production:** Employs an architecture containing stubs.

---

## 1. Modular Architecture

StrictPro uses a split library dependency structure to ensure no development helper APIs or layout assets leak into production.

### Gradle Dependencies Configuration
```kotlin
dependencies {
    val libVersion = "1.0.0"
    // Debug builds get the fully functional library and UI viewer
    debugImplementation("com.github.tberchanov.StrictPro:strictpro:$libVersion")
    debugImplementation("com.github.tberchanov.StrictPro:strictpro.ui:$libVersion")

    // Release/Production builds get zero-dependency empty stubs to optimize size
    releaseImplementation("com.github.tberchanov.StrictPro:strictpro.stubs:$libVersion")
    releaseImplementation("com.github.tberchanov.StrictPro:strictpro.ui.stubs:$libVersion")
}
```

---

## 2. Dynamic Violation Whitelisting (`ViolationWhiteList`)

The `ViolationWhiteList` resolves StrictMode's rigid "all-or-nothing" enforcement. It dynamically routes specific stack traces to specialized actions (e.g. log instead of crash).

### Whitelist Filtering DSL
```kotlin
StrictPro.setThreadPolicy(
    StrictPro.ThreadPolicy.Builder()
        .detectAll()
        .penaltyDeath() // Default action: crash
        .setWhiteList {
            // Case 1: Bypass/Ignore violation completely if stack contains specific framework substring
            contains("android.webkit.WebViewDatabase", null)

            // Case 2: Downgrade penalty to Dialog (instead of Death) for a specific known base64 stack signature
            base64("aGFzaF9zdGFja190cmFjZV9oZXJl...", ViolationPenalty.Dialog)

            // Case 3: Apply custom matching logic using an inline condition
            condition { violation ->
                if (violation.stackTrace.any { it.className.contains("OkHttp") }) {
                    ViolationPenalty.Log // Downgrade to logging only
                } else {
                    null // Keep default (Death)
                }
            }
        }
        .build()
)
```

### Whitelist Matching Mechanics
- Under Android P (API 28)+, StrictPro registers a single global listener:
  `ThreadPolicy.Builder.penaltyListener(MainThreadExecutor()) { violation -> ... }`
- Stack traces are converted to strings via `violation.stackTraceToStringCompat()`.
- The library evaluates whitelist conditions sequentially:
  - Match is found -> returned penalty is collected.
  - If the match returns a penalty that is `Ignore` (represented as `ViolationPenalty.Ignore`), all other penalties are ignored for that violation.
- If no whitelist match is found, the builder defaults to the set of default penalties configured (e.g. `penaltyDeath()`).
- On older platforms (API < 28) where listeners are unsupported, whitelists are bypassed and standard StrictMode fallback penalties are applied.

---

## 3. Custom Penalty Executors

StrictMode violations intercept through a `CompositePenaltyExecutor` which executes penalties in order of increasing severity:

```
CompositePenaltyExecutor
  └── 1. LogPenaltyExecutor       (Dump trace to logcat)
  └── 2. DropBoxPenaltyExecutor   (Record to OS dropbox)
  └── 3. DialogPenaltyExecutor    (Show dialog in app - rate limited)
  └── 4. FlashScreenPenaltyExecutor (Flash red UI boundary)
  └── 5. DeathPenaltyExecutor     (Kill process - MUST be last)
```

Executing `DeathPenaltyExecutor` last allows logs and dialog triggers to complete before process termination.
- **Activity Context Collection:** To show dialogs/flash screens, `StrictPro` registers `registerActivityLifecycleCallbacks` internally inside `listenActivities()` to capture a `WeakReference<Activity>` on `onActivityPreCreated` and `onActivityResumed`.
- **Background Execution:** Telemetry logging and uploads are executed on a single-thread background executor to prevent the act of logging/reporting from triggering nested StrictMode violations on the UI thread.
