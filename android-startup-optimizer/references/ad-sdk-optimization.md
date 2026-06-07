# Ad SDK Optimization

Ad SDKs are the #1 cause of startup bloat in monetized apps. Optimize without sacrificing revenue.

## The Problem

**Typical ad SDK initialization:**
- 5-10 ContentProviders registered
- Main thread blocking for 500-2000ms
- Synchronous disk I/O for configuration
- Native library loading (System.loadLibrary)
- Network handshakes for bidding adapters

**Impact:** 2-8 seconds added to cold start time.

## Google Mobile Ads (AdMob/Ad Manager)

### Enable Background Initialization

```xml
<!-- AndroidManifest.xml -->
<application>
    <!-- GMA SDK 21.0.0+ -->
    <meta-data
        android:name="com.google.android.gms.ads.flag.OPTIMIZE_INITIALIZATION"
        android:value="true" />
    
    <meta-data
        android:name="com.google.android.gms.ads.flag.OPTIMIZE_AD_LOADING"
        android:value="true" />
</application>
```

**Note:** GMA SDK 24.0.0+ enables these by default.

### Async Initialization

```kotlin
class MyApp : Application() {
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        
        // Initialize in background
        applicationScope.launch {
            MobileAds.initialize(this@MyApp) { initStatus ->
                Log.d("AdMob", "Initialized: ${initStatus.adapterStatusMap}")
            }
        }
    }
}
```

### Lazy Ad Loading

```kotlin
@Composable
fun HomeScreen() {
    var adLoaded by remember { mutableStateOf(false) }
    
    LaunchedEffect(Unit) {
        // Wait for screen to render first
        delay(500)
        adLoaded = true
    }
    
    Column {
        MainContent()
        
        if (adLoaded) {
            BannerAd()
        }
    }
}
```

## App Open Ads (Splash Ads)

### Correct Implementation

```kotlin
class MyApp : Application() {
    
    private var appOpenAdManager: AppOpenAdManager? = null
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize SDK first
        applicationScope.launch {
            MobileAds.initialize(this@MyApp)
            
            // Then load app open ad
            appOpenAdManager = AppOpenAdManager(this@MyApp)
        }
        
        // Register lifecycle observer
        ProcessLifecycleOwner.get().lifecycle.addObserver(
            AppOpenAdLifecycleObserver()
        )
    }
}

class AppOpenAdManager(private val app: Application) {
    
    private var appOpenAd: AppOpenAd? = null
    private var isLoadingAd = false
    private var loadTime: Long = 0
    
    fun loadAd() {
        if (isLoadingAd || isAdAvailable()) return
        
        isLoadingAd = true
        val request = AdRequest.Builder().build()
        
        AppOpenAd.load(
            app,
            "ca-app-pub-3940256099942544/9257395921", // Test ID
            request,
            object : AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: AppOpenAd) {
                    appOpenAd = ad
                    isLoadingAd = false
                    loadTime = System.currentTimeMillis()
                }
                
                override fun onAdFailedToLoad(error: LoadAdError) {
                    isLoadingAd = false
                }
            }
        )
    }
    
    private fun isAdAvailable(): Boolean {
        return appOpenAd != null && wasLoadTimeLessThanNHoursAgo(4)
    }
    
    private fun wasLoadTimeLessThanNHoursAgo(hours: Long): Boolean {
        val dateDifference = System.currentTimeMillis() - loadTime
        val numMilliSecondsPerHour = 3600000L
        return dateDifference < numMilliSecondsPerHour * hours
    }
    
    fun showAdIfAvailable(activity: Activity, onAdDismissed: () -> Unit) {
        if (!isAdAvailable()) {
            onAdDismissed()
            loadAd()
            return
        }
        
        appOpenAd?.fullScreenContentCallback = object : FullScreenContentCallback() {
            override fun onAdDismissedFullScreenContent() {
                appOpenAd = null
                onAdDismissed()
                loadAd()
            }
            
            override fun onAdFailedToShowFullScreenContent(error: AdError) {
                appOpenAd = null
                onAdDismissed()
                loadAd()
            }
        }
        
        appOpenAd?.show(activity)
    }
}

class AppOpenAdLifecycleObserver : DefaultLifecycleObserver {
    override fun onStart(owner: LifecycleOwner) {
        val activity = (owner as? ComponentActivity) ?: return
        val app = activity.application as MyApp
        
        // Show ad with timeout
        val handler = Handler(Looper.getMainLooper())
        var adShown = false
        
        handler.postDelayed({
            if (!adShown) {
                // Timeout - proceed without ad
                proceedToApp(activity)
            }
        }, 2000) // 2 second timeout
        
        app.appOpenAdManager?.showAdIfAvailable(activity) {
            adShown = true
            handler.removeCallbacksAndMessages(null)
            proceedToApp(activity)
        }
    }
    
    private fun proceedToApp(activity: Activity) {
        // Continue to main content
    }
}
```

### Critical: Implement Timeout

```kotlin
// NEVER wait indefinitely for ads
fun showAdWithTimeout(activity: Activity, timeoutMs: Long = 2000) {
    var adCompleted = false
    
    // Set timeout
    Handler(Looper.getMainLooper()).postDelayed({
        if (!adCompleted) {
            Log.w("Ads", "Ad timeout - proceeding")
            proceedToApp()
        }
    }, timeoutMs)
    
    // Try to show ad
    appOpenAdManager?.showAdIfAvailable(activity) {
        adCompleted = true
        proceedToApp()
    }
}
```

## Mediation Networks

### AppLovin MAX

```kotlin
class MyApp : Application() {
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        
        // Background initialization
        applicationScope.launch {
            AppLovinSdk.getInstance(this@MyApp).apply {
                mediationProvider = "max"
                initializeSdk { config ->
                    Log.d("AppLovin", "Initialized")
                }
            }
        }
    }
}
```

### Unity LevelPlay (IronSource)

```kotlin
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        // Defer initialization
        registerActivityLifecycleCallbacks(object : ActivityLifecycleCallbacks {
            override fun onActivityCreated(activity: Activity, bundle: Bundle?) {
                if (!ironSourceInitialized) {
                    IronSource.init(
                        activity,
                        "YOUR_APP_KEY",
                        IronSource.AD_UNIT.INTERSTITIAL,
                        IronSource.AD_UNIT.REWARDED_VIDEO
                    )
                    ironSourceInitialized = true
                }
                unregisterActivityLifecycleCallbacks(this)
            }
            // ... other callbacks
        })
    }
}
```

## Adapter Initialization Times

Based on real-world measurements:

| Network | Avg Init Time | Recommendation |
|---------|---------------|----------------|
| Mintegral | 400ms | Safe for startup |
| InMobi | 1.2s | Background init |
| AdMob | 1.3s | Background init |
| Chartboost | 1.4s | Background init |
| IronSource | 2.6s | Defer until needed |
| Vungle | 4.8s | Defer until needed |
| AppLovin | 6.4s | Defer until needed |
| Unity Ads | 7.5s | Defer until needed |

**Strategy:** Initialize fast networks early, defer slow ones.

## Bidding vs Waterfall

### Waterfall (Sequential) - SLOW

```
Request Ad → Network 1 (timeout) → Network 2 (timeout) → Network 3 (success)
Total time: 3-10 seconds
```

### Bidding (Parallel) - FAST

```
Request Ad → All networks bid simultaneously → Winner selected
Total time: 500ms - 2 seconds
```

**Recommendation:** Use bidding-only mediation for faster ad loading.

## Disable Unused Ad Formats

```kotlin
// Only initialize formats you actually use
MobileAds.initialize(this) { initStatus ->
    // Disable unused adapters
    val disabledAdapters = listOf(
        "com.google.ads.mediation.facebook.FacebookAdapter",
        "com.google.ads.mediation.vungle.VungleAdapter"
    )
    
    disabledAdapters.forEach { adapter ->
        MobileAds.disableMediationAdapterInitialization(this, adapter)
    }
}
```

## Remove Unused Mediation Adapters

```kotlin
// build.gradle.kts
dependencies {
    // Only include adapters you use
    implementation("com.google.android.gms:play-services-ads:23.0.0")
    
    // Remove unused adapters
    // implementation("com.google.ads.mediation:facebook:6.16.0.0")
    // implementation("com.google.ads.mediation:vungle:7.1.0.0")
}
```

## Banner Ad Lazy Loading

```kotlin
@Composable
fun BannerAd(adUnitId: String) {
    var shouldLoad by remember { mutableStateOf(false) }
    
    // Only load when visible
    LaunchedEffect(Unit) {
        delay(1000) // Wait for main content
        shouldLoad = true
    }
    
    if (shouldLoad) {
        AndroidView(
            factory = { context ->
                AdView(context).apply {
                    setAdSize(AdSize.BANNER)
                    this.adUnitId = adUnitId
                    loadAd(AdRequest.Builder().build())
                }
            }
        )
    } else {
        // Placeholder
        Box(modifier = Modifier.height(50.dp))
    }
}
```

## Preload Strategy

```kotlin
class AdPreloader(private val context: Context) {
    
    private val interstitialAd = MutableStateFlow<InterstitialAd?>(null)
    
    init {
        // Preload after startup completes
        Handler(Looper.getMainLooper()).postDelayed({
            preloadInterstitial()
        }, 5000) // 5 seconds after app start
    }
    
    private fun preloadInterstitial() {
        InterstitialAd.load(
            context,
            "ca-app-pub-3940256099942544/1033173712",
            AdRequest.Builder().build(),
            object : InterstitialAdLoadCallback() {
                override fun onAdLoaded(ad: InterstitialAd) {
                    interstitialAd.value = ad
                }
            }
        )
    }
    
    fun showInterstitial(activity: Activity, onDismissed: () -> Unit) {
        interstitialAd.value?.show(activity)
        onDismissed()
        preloadInterstitial() // Reload for next time
    }
}
```

## Monitoring Ad Impact

```kotlin
class MyApp : Application() {
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        
        val startTime = System.currentTimeMillis()
        
        applicationScope.launch {
            MobileAds.initialize(this@MyApp)
            
            val duration = System.currentTimeMillis() - startTime
            Log.d("Ads", "Initialization took ${duration}ms")
            
            // Send to analytics
            analytics.logEvent("ad_init_duration", bundleOf("ms" to duration))
        }
    }
}
```

## Best Practices Summary

1. **Always use background initialization** - Never block main thread
2. **Implement timeouts** - Don't wait forever for ads
3. **Defer heavy networks** - Initialize slow adapters later
4. **Use bidding** - Parallel requests are faster than waterfall
5. **Remove unused adapters** - Less code = faster startup
6. **Lazy load banners** - Wait for main content to render
7. **Monitor performance** - Track initialization times
8. **Test on low-end devices** - Ads hit budget phones hardest

## Migration Checklist

- [ ] Enable GMA SDK optimization flags
- [ ] Move MobileAds.initialize() to background thread
- [ ] Implement app open ad timeout (2 seconds max)
- [ ] Remove unused mediation adapters
- [ ] Switch to bidding-only mediation
- [ ] Defer banner ad loading (1 second delay)
- [ ] Add ad initialization telemetry
- [ ] Test on Android Go devices
- [ ] Measure before/after with Macrobenchmark
- [ ] Monitor Android Vitals for improvements
