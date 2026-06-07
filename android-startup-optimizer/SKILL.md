---
name: android-startup-optimizer
description: Expert Android app startup performance optimization skill. Use when analyzing or improving Android app cold start, warm start, or hot start times. Applies to projects using Jetpack Compose, Hilt/Dagger, ContentProviders, ad SDKs, or any Android initialization bottlenecks. Triggers on phrases like "startup time", "app launch", "cold start", "slow startup", "initialization performance", "TTID", "TTFD", "baseline profiles", "startup profiles", "R8 optimization", "app startup library", or when analyzing Application.onCreate(), Activity.onCreate(), or SDK initialization patterns.
---

# Android Startup Performance Optimizer

<instructions>
Follow this structured workflow to diagnose, measure, and optimize Android application startup performance. Prioritize asynchronous lazy initialization and platform-native telemetry.
</instructions>

## Android Vitals Thresholds

| Type | Target | Impact |
|------|--------|--------|
| Cold Start | <5.0s | Critical (vitals threshold) |
| Warm Start | <2.0s | User experience degradation |
| Hot Start | <1.5s | User experience degradation |

Exceeding these leads to increased user abandonment and lower Google Play Store rankings.

## Optimization Process

1. **Measure**: Use Macrobenchmark, Perfetto/Android Studio Profiler, and Android Vitals. Never optimize blindly.
2. **Quick Wins**: Enable R8 Full Mode, Baseline Profiles, Startup Profiles, and DEX layout optimizations.
3. **Architectural**: Eliminate main-thread blocking calls in `Application.onCreate()`, `Activity.onCreate()`, and before first frame rendering.
4. **Ad SDKs**: Utilize lazy-loading, background initialization flags, and timeouts.
5. **Monitor**: Integrate Macrobenchmarking in CI, enable StrictMode in debug, and use `ApplicationStartInfo` telemetry (Android 15+).

## Diagnostic Checklist

- **Application.onCreate()**: Check for blocking disk I/O, network calls, eager heavy singleton creation, multiple `ContentProvider` initializations, or blocking ad SDK initializations.
- **Dependency Injection**: Avoid injecting heavy dependencies eagerly; wrap optional/deferred dependencies in `Lazy<T>`.
- **Activity.onCreate()**: Audit complex layout inflation, synchronous database/file access, heavy initial composition, or bitmap decoding on the main thread.

## Implementation Patterns

```kotlin
// BAD: blocking Application.onCreate()
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Firebase.initialize(this)
        MobileAds.initialize(this) // blocks main thread
        val config = File(filesDir, "config.json").readText() // disk I/O on main thread
    }
}

// GOOD: async + lazy application initialization
class MyApp : Application() {
    val container: AppContainer by lazy { AppContainerImpl(this) }
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        applicationScope.launch {
            Firebase.initialize(this@MyApp)
            MobileAds.initialize(this@MyApp)
        }
    }
}

// GOOD: Lazy Hilt injection in ViewModel
@HiltViewModel
class MainViewModel @Inject constructor(
    private val userRepository: UserRepository,           // eager — needed immediately
    private val analyticsTracker: Lazy<AnalyticsTracker>, // lazy — deferred instantiation
) : ViewModel()

// GOOD: App Startup library initializer
class AdMobInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        Executors.newSingleThreadExecutor().execute { MobileAds.initialize(context) }
    }
    override fun dependencies() = emptyList<Class<Initializer<*>>>()
}
```

## Success Metrics

| Metric | Target | Tool |
|--------|--------|------|
| Cold Start p50 | <2.0s | Macrobenchmark |
| Cold Start p90 | <3.5s | Android Vitals |
| TTID | <1.5s | `reportFullyDrawn()` |
| TTFD | <2.5s | Custom telemetry |
| Main thread blocking | <100ms total | Profiler / Perfetto |

## Platform Notes

- **Android 15 (API 35)**: 16 KB page support (requires native library rebuilds); `ApplicationStartInfo` API; foreground service limitations.
- **Android 16 (API 36)**: `ProfilingManager` API for system-triggered traces; CPU/GPU headroom APIs for adaptive quality; `getStartComponent()`.

## Reference Files

- [references/measurement.md](references/measurement.md) — Macrobenchmark, Perfetto, Android Vitals
- [references/r8-optimization.md](references/r8-optimization.md) — R8 full mode configuration
- [references/baseline-profiles.md](references/baseline-profiles.md) — Profile generation and validation
- [references/startup-profiles.md](references/startup-profiles.md) — DEX layout optimization
- [references/architectural-patterns.md](references/architectural-patterns.md) — App Startup, lazy injection, and threading
- [references/ad-sdk-optimization.md](references/ad-sdk-optimization.md) — Ad network initialization strategies
- [references/compose-optimization.md](references/compose-optimization.md) — Jetpack Compose composition phases
- [references/platform-updates.md](references/platform-updates.md) — Android 15/16 startup changes

<constraints>
- Never recommend using `lifecycleScope` inside `Application.onCreate()`. You should recommend a custom `CoroutineScope(SupervisorJob() + Dispatchers.Default)` instead.
- For Android 15+, you must recommend the `ApplicationStartInfo` API for telemetry and the `ProfilingManager` API for system-triggered field traces.
- For Android 16+, you should recommend getStartComponent() on `ApplicationStartInfo` for component-specific optimizations.
- You must only wrap Hilt/Dagger dependencies in `Lazy<T>` if they are not immediately needed.
</constraints>
