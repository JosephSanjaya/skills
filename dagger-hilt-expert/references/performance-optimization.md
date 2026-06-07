# Performance Optimization and Startup Latency

## Startup Performance Problems

### Anti-Pattern: Eager Initialization in Application.onCreate()

```kotlin
@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var analytics: Analytics
    @Inject lateinit var crashReporter: CrashReporter
    @Inject lateinit var remoteConfig: RemoteConfig
    @Inject lateinit var database: AppDatabase
    @Inject lateinit var imageLoader: ImageLoader
    
    override fun onCreate() {
        super.onCreate()
        // ❌ All dependencies initialized immediately
        // Blocks UI thread during app startup
        analytics.initialize()
        crashReporter.initialize()
        remoteConfig.fetch()
    }
}
```

**Problem:** User sees blank screen while all services initialize.

## Lazy Injection Pattern

### Lazy<T>: Defer Until First Use

```kotlin
@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var analytics: Lazy<Analytics>
    @Inject lateinit var crashReporter: Lazy<CrashReporter>
    @Inject lateinit var remoteConfig: Lazy<RemoteConfig>
    
    override fun onCreate() {
        super.onCreate()
        
        // ✅ Only crash reporter initialized immediately (critical)
        crashReporter.get().initialize()
        
        // ✅ Others deferred to background
        lifecycleScope.launch {
            delay(100) // Let UI render first
            analytics.get().initialize()
            remoteConfig.get().fetch()
        }
    }
}
```

### Module Configuration for Lazy

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AnalyticsModule {
    @Provides
    @Singleton
    fun provideAnalytics(@ApplicationContext context: Context): Analytics {
        // This won't be called until analytics.get() is invoked
        return FirebaseAnalytics.getInstance(context)
    }
}

// Injection site
class FeatureViewModel @Inject constructor(
    private val analytics: Lazy<Analytics>  // ✅ Lazy wrapper
) : ViewModel() {
    
    fun trackEvent(event: String) {
        analytics.get().logEvent(event)  // Initialized on first call
    }
}
```

## Provider<T>: New Instance Per Call

### Use Case: Breaking Circular Dependencies

```kotlin
// ❌ Circular dependency
class ServiceA @Inject constructor(
    private val serviceB: ServiceB
)

class ServiceB @Inject constructor(
    private val serviceA: ServiceA  // Error: circular dependency
)

// ✅ Break with Provider
class ServiceA @Inject constructor(
    private val serviceB: ServiceB
)

class ServiceB @Inject constructor(
    private val serviceAProvider: Provider<ServiceA>
) {
    fun doSomething() {
        val serviceA = serviceAProvider.get()  // Get instance when needed
        serviceA.process()
    }
}
```

### Use Case: Short-Lived Objects

```kotlin
class RequestHandler @Inject constructor(
    private val requestProcessorProvider: Provider<RequestProcessor>
) {
    fun handle(request: Request) {
        // New processor for each request
        val processor = requestProcessorProvider.get()
        processor.process(request)
    }
}
```

## Startup Profiling

### Measure with Android Studio Profiler

```kotlin
@HiltAndroidApp
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        
        val startTime = System.currentTimeMillis()
        
        // Your initialization
        
        val duration = System.currentTimeMillis() - startTime
        Log.d("Startup", "Application.onCreate took ${duration}ms")
    }
}
```

### Macrobenchmark for Startup Metrics

```kotlin
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()
    
    @Test
    fun startup() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric()),
        iterations = 5,
        startupMode = StartupMode.COLD
    ) {
        pressHome()
        startActivityAndWait()
    }
}
```

## Scoping Impact on Performance

### Unscoped: Fastest for Stateless Objects

```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface MapperModule {
    @Binds
    fun bindUserMapper(impl: UserMapperImpl): UserMapper  // No scope
}

// Generated code: Direct instantiation
public UserMapper get() {
    return new UserMapperImpl();
}
```

### Scoped: DoubleCheck Overhead

```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {
    @Binds
    @Singleton
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}

// Generated code: Thread-safe singleton check
public UserRepository get() {
    Object local = instance;
    if (local == null) {
        synchronized (this) {
            local = instance;
            if (local == null) {
                instance = local = new UserRepositoryImpl(...);
            }
        }
    }
    return (UserRepository) local;
}
```

**Rule:** Only scope when necessary (state sharing, expensive construction, synchronization).

## Async Initialization Pattern

### Background Initializer

```kotlin
interface Initializer {
    suspend fun initialize()
}

class AnalyticsInitializer @Inject constructor(
    private val analytics: Analytics
) : Initializer {
    override suspend fun initialize() {
        withContext(Dispatchers.IO) {
            analytics.initialize()
        }
    }
}

@Module
@InstallIn(SingletonComponent::class)
interface InitializerModule {
    @Binds
    @IntoSet
    fun bindAnalyticsInitializer(impl: AnalyticsInitializer): Initializer
}

@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var initializers: Set<@JvmSuppressWildcards Initializer>
    
    override fun onCreate() {
        super.onCreate()
        
        lifecycleScope.launch {
            initializers.forEach { it.initialize() }
        }
    }
}
```

## Multibinding for Modular Initialization

### Pattern: Collect Initializers from Multiple Modules

```kotlin
// Core module
@Module
@InstallIn(SingletonComponent::class)
interface CoreInitializerModule {
    @Binds
    @IntoSet
    fun bindCrashReporter(impl: CrashReporterInitializer): Initializer
}

// Analytics module
@Module
@InstallIn(SingletonComponent::class)
interface AnalyticsInitializerModule {
    @Binds
    @IntoSet
    fun bindAnalytics(impl: AnalyticsInitializer): Initializer
}

// Feature module
@Module
@InstallIn(SingletonComponent::class)
interface FeatureInitializerModule {
    @Binds
    @IntoSet
    fun bindFeature(impl: FeatureInitializer): Initializer
}

// All automatically collected into Set<Initializer>
```

## WorkManager Integration for Heavy Initialization

### Pattern: Defer to Background Worker

```kotlin
@HiltWorker
class InitializationWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val remoteConfig: RemoteConfig,
    private val database: AppDatabase
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        return try {
            remoteConfig.fetchAndActivate()
            database.runMigrations()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}

@HiltAndroidApp
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        
        // Schedule background initialization
        val request = OneTimeWorkRequestBuilder<InitializationWorker>()
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .build()
        
        WorkManager.getInstance(this).enqueue(request)
    }
}
```

## Memory Optimization

### Avoid Singleton for Feature-Specific Dependencies

```kotlin
// ❌ Bad: Onboarding stays in memory forever
@Module
@InstallIn(SingletonComponent::class)
object OnboardingModule {
    @Provides
    @Singleton
    fun provideOnboardingManager(): OnboardingManager = OnboardingManagerImpl()
}

// ✅ Good: Cleaned up when activity finishes
@Module
@InstallIn(ActivityComponent::class)
object OnboardingModule {
    @Provides
    @ActivityScoped
    fun provideOnboardingManager(): OnboardingManager = OnboardingManagerImpl()
}
```

### Leak Detection with LeakCanary

```kotlin
// build.gradle.kts
dependencies {
    debugImplementation("com.squareup.leakcanary:leakcanary-android:2.12")
}

// Automatically detects leaks from scoped dependencies
```

## FastInit Mode (Hilt Default)

Hilt enables `fastInit` by default for monolithic components, optimizing component creation speed.

### What FastInit Does
- Reduces generated code size
- Optimizes component initialization
- Shares component instances across Activities/Fragments

### Verify FastInit is Enabled
```kotlin
// build.gradle.kts
hilt {
    enableAggregatingTask = true  // Enables FastInit
}
```

## Baseline Profiles for Dagger Code

### Generate Baseline Profile

```kotlin
// baselineprofile/build.gradle.kts
dependencies {
    implementation("androidx.benchmark:benchmark-macro-junit4:1.2.0")
}

// BaselineProfileGenerator.kt
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {
    @get:Rule
    val rule = BaselineProfileRule()
    
    @Test
    fun generate() = rule.collect(
        packageName = "com.example.app",
        includeInStartupProfile = true
    ) {
        pressHome()
        startActivityAndWait()
        
        // Navigate through critical paths
        device.findObject(By.res("loginButton")).click()
        device.wait(Until.hasObject(By.res("homeScreen")), 5000)
    }
}
```

Baseline profiles pre-compile Dagger-generated code, reducing startup JIT overhead.

## Monitoring and Alerting

### Track Startup Metrics in Production

```kotlin
@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var analytics: Lazy<Analytics>
    
    override fun onCreate() {
        super.onCreate()
        
        val startTime = System.currentTimeMillis()
        
        // Critical initialization only
        
        val duration = System.currentTimeMillis() - startTime
        
        // Report to analytics
        lifecycleScope.launch {
            analytics.get().logEvent("app_startup", mapOf(
                "duration_ms" to duration,
                "cold_start" to isColdStart()
            ))
        }
    }
    
    private fun isColdStart(): Boolean {
        // Check if process was just created
        return true  // Implement actual logic
    }
}
```

## Performance Checklist

- [ ] Use Lazy<T> for non-critical dependencies
- [ ] Move heavy initialization to background threads
- [ ] Avoid Singleton for feature-specific dependencies
- [ ] Profile startup with Android Studio Profiler
- [ ] Measure with Macrobenchmark
- [ ] Only scope when necessary (state, cost, sync)
- [ ] Use WorkManager for heavy background initialization
- [ ] Generate baseline profiles for Dagger code
- [ ] Monitor startup metrics in production
- [ ] Verify FastInit is enabled
- [ ] Use Provider<T> to break circular dependencies
- [ ] Implement modular initialization with multibinding
