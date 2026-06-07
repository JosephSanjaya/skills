# Architectural Patterns for Fast Startup

## Jetpack App Startup Library

Consolidate all ContentProvider initializations into a single provider.

### Problem: Multiple ContentProviders

```kotlin
// Each SDK registers its own provider - expensive!
// AndroidManifest.xml
<provider
    android:name="com.firebase.FirebaseInitProvider"
    android:authorities="${applicationId}.firebaseinitprovider" />
<provider
    android:name="com.google.android.gms.ads.MobileAdsInitProvider"
    android:authorities="${applicationId}.mobileadsinitprovider" />
<provider
    android:name="com.analytics.AnalyticsInitProvider"
    android:authorities="${applicationId}.analyticsinitprovider" />
```

### Solution: App Startup

```kotlin
// 1. Add dependency
dependencies {
    implementation("androidx.startup:startup-runtime:1.1.1")
}

// 2. Create initializers
class FirebaseInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        Firebase.initialize(context)
    }
    override fun dependencies() = emptyList<Class<out Initializer<*>>>()
}

class AdMobInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        // Background initialization
        Executors.newSingleThreadExecutor().execute {
            MobileAds.initialize(context)
        }
    }
    override fun dependencies() = listOf(FirebaseInitializer::class.java)
}

// 3. Register in manifest
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    android:exported="false"
    tools:node="merge">
    
    <meta-data
        android:name="com.example.FirebaseInitializer"
        android:value="androidx.startup" />
    <meta-data
        android:name="com.example.AdMobInitializer"
        android:value="androidx.startup" />
</provider>

// 4. Disable automatic SDK providers
<provider
    android:name="com.google.android.gms.ads.MobileAdsInitProvider"
    android:authorities="${applicationId}.mobileadsinitprovider"
    tools:node="remove" />
```

### Lazy Initialization

```kotlin
// Defer until actually needed
class AnalyticsInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        // Don't initialize here - just return
    }
    override fun dependencies() = emptyList<Class<out Initializer<*>>>()
}

// Initialize manually when needed
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        // Initialize only when user performs trackable action
        registerActivityLifecycleCallbacks(object : ActivityLifecycleCallbacks {
            override fun onActivityResumed(activity: Activity) {
                AppInitializer.getInstance(this@MyApp)
                    .initializeComponent(AnalyticsInitializer::class.java)
                unregisterActivityLifecycleCallbacks(this)
            }
            // ... other callbacks
        })
    }
}
```

## Lazy Dependency Injection (Hilt/Dagger)

### Problem: Eager Singleton Creation

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideDatabase(app: Application): AppDatabase {
        // Created immediately at app startup!
        return Room.databaseBuilder(
            app,
            AppDatabase::class.java,
            "app-db"
        ).build()
    }
    
    @Provides
    @Singleton
    fun provideAnalytics(): AnalyticsTracker {
        // Heavy initialization on main thread!
        return AnalyticsTracker.Builder()
            .withConfig(loadConfig())
            .build()
    }
}
```

### Solution: Lazy Injection

```kotlin
@HiltViewModel
class MainViewModel @Inject constructor(
    // Eager - needed immediately
    private val userRepository: UserRepository,
    
    // Lazy - created only when first accessed
    private val database: Lazy<AppDatabase>,
    private val analytics: Lazy<AnalyticsTracker>,
    
    // Provider - new instance each time
    private val heavyFeature: Provider<HeavyFeature>
) : ViewModel() {
    
    fun loadData() {
        viewModelScope.launch {
            // Database created here, not at startup
            val data = database.get().userDao().getAll()
            updateState(data)
        }
    }
    
    fun trackEvent(event: String) {
        // Analytics created here, not at startup
        analytics.get().track(event)
    }
}
```

### Scoped Dependencies

```kotlin
// BAD: Everything in SingletonComponent
@Module
@InstallIn(SingletonComponent::class)
object BadModule {
    @Provides
    @Singleton
    fun provideProfileFeature(): ProfileFeature = ProfileFeature()
}

// GOOD: Scope to where it's actually used
@Module
@InstallIn(ActivityRetainedComponent::class)
object GoodModule {
    @Provides
    @ActivityRetainedScoped
    fun provideProfileFeature(): ProfileFeature = ProfileFeature()
}
```

## Background Threading

### Coroutines for Async Init

```kotlin
class MyApp : Application() {
    
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    
    override fun onCreate() {
        super.onCreate()
        
        // Launch non-blocking initializations
        applicationScope.launch {
            initializeLogging()
        }
        
        applicationScope.launch {
            initializeAnalytics()
        }
        
        applicationScope.launch {
            preloadCriticalData()
        }
    }
    
    private suspend fun initializeLogging() = withContext(Dispatchers.IO) {
        Timber.plant(Timber.DebugTree())
        // Load log configuration from disk
        val config = File(filesDir, "log_config.json").readText()
        LogConfig.apply(config)
    }
    
    private suspend fun preloadCriticalData() = withContext(Dispatchers.IO) {
        // Warm up caches
        userRepository.preloadCurrentUser()
        configRepository.fetchRemoteConfig()
    }
}
```

### WorkManager for Deferred Init

```kotlin
// For truly non-critical initialization
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        // Schedule background work
        val workRequest = OneTimeWorkRequestBuilder<InitializationWorker>()
            .setInitialDelay(5, TimeUnit.SECONDS)
            .build()
        
        WorkManager.getInstance(this).enqueue(workRequest)
    }
}

class InitializationWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        // Initialize non-critical SDKs
        initializeImageCache()
        initializeCrashReporting()
        return Result.success()
    }
}
```

## Data Loading Strategies

### Cache-First Rendering

```kotlin
@Composable
fun MainScreen(viewModel: MainViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    
    LaunchedEffect(Unit) {
        // Load fresh data in background
        viewModel.refreshData()
    }
    
    when (state) {
        is Loading -> {
            // Show cached data immediately if available
            val cachedData = viewModel.getCachedData()
            if (cachedData != null) {
                ContentScreen(cachedData)
                // Show refresh indicator
                LinearProgressIndicator()
            } else {
                LoadingScreen()
            }
        }
        is Success -> ContentScreen(state.data)
        is Error -> ErrorScreen(state.message)
    }
}
```

### Pagination for Large Lists

```kotlin
@Composable
fun FeedScreen(viewModel: FeedViewModel = hiltViewModel()) {
    val items = viewModel.pagingData.collectAsLazyPagingItems()
    
    LazyColumn {
        items(
            count = items.itemCount,
            key = { items[it]?.id ?: it }
        ) { index ->
            items[index]?.let { item ->
                FeedItem(item)
            }
        }
    }
}

@HiltViewModel
class FeedViewModel @Inject constructor(
    private val repository: FeedRepository
) : ViewModel() {
    
    val pagingData = Pager(
        config = PagingConfig(
            pageSize = 20,
            prefetchDistance = 5,
            initialLoadSize = 20
        )
    ) {
        repository.getFeedPagingSource()
    }.flow.cachedIn(viewModelScope)
}
```

## Deferred Feature Loading

### Feature Modules

```kotlin
// Dynamic feature module
// feature-profile/build.gradle.kts
plugins {
    id("com.android.dynamic-feature")
}

android {
    namespace = "com.example.feature.profile"
}

dependencies {
    implementation(project(":app"))
}

// Load on demand
class MainActivity : ComponentActivity() {
    private val splitInstallManager by lazy {
        SplitInstallManagerFactory.create(this)
    }
    
    fun loadProfileFeature() {
        val request = SplitInstallRequest.newBuilder()
            .addModule("feature-profile")
            .build()
        
        splitInstallManager.startInstall(request)
            .addOnSuccessListener {
                // Feature loaded, navigate to it
                navigateToProfile()
            }
    }
}
```

### Conditional Initialization

```kotlin
class MyApp : Application() {
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        
        // Only initialize features based on user state
        applicationScope.launch {
            val user = userRepository.getCurrentUser()
            
            if (user.isPremium) {
                initializePremiumFeatures()
            }
            
            if (user.hasNotificationsEnabled) {
                initializePushNotifications()
            }
        }
    }
}
```

## Memory Management

### Avoid Heavy Object Creation

```kotlin
// BAD: Creates heavy objects at startup
class MyApp : Application() {
    val heavyCache = LruCache<String, Bitmap>(1024 * 1024 * 50) // 50MB
    val complexGraph = buildComplexDataStructure()
    
    override fun onCreate() {
        super.onCreate()
        // These are created immediately!
    }
}

// GOOD: Lazy initialization
class MyApp : Application() {
    val heavyCache by lazy {
        LruCache<String, Bitmap>(1024 * 1024 * 50)
    }
    
    val complexGraph by lazy {
        buildComplexDataStructure()
    }
    
    override fun onCreate() {
        super.onCreate()
        // Nothing created until accessed
    }
}
```

### Bitmap Optimization

```kotlin
// Use Coil for async image loading
@Composable
fun ProfileImage(url: String) {
    AsyncImage(
        model = ImageRequest.Builder(LocalContext.current)
            .data(url)
            .crossfade(true)
            .size(200, 200) // Resize to actual display size
            .build(),
        contentDescription = "Profile"
    )
}

// Configure Coil for startup
class MyApp : Application(), ImageLoaderFactory {
    override fun newImageLoader(): ImageLoader {
        return ImageLoader.Builder(this)
            .memoryCache {
                MemoryCache.Builder(this)
                    .maxSizePercent(0.25) // Use 25% of app memory
                    .build()
            }
            .diskCache {
                DiskCache.Builder()
                    .directory(cacheDir.resolve("image_cache"))
                    .maxSizeBytes(50 * 1024 * 1024) // 50MB
                    .build()
            }
            .build()
    }
}
```

## Summary

**Key Principles:**
1. **Consolidate** - Use App Startup for all ContentProviders
2. **Defer** - Lazy injection, late initialization
3. **Background** - Coroutines for I/O and heavy work
4. **Cache** - Show cached data while loading fresh
5. **Scope** - Don't put everything in SingletonComponent
6. **Measure** - Profile before and after changes
