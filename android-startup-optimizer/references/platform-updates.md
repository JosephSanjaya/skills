# Android 15 & 16 Platform Updates

New APIs and platform behaviors that impact startup performance.

## Android 15 (API 35)

### 16 KB Page Size Support

**Impact:** 30% faster app launch under memory pressure, 4.5% lower power consumption.

**What Changed:**
- Traditional Android uses 4 KB memory pages
- Android 15 adds support for 16 KB pages on compatible devices
- Larger pages reduce TLB (Translation Lookaside Buffer) misses
- Better memory locality for app code

**Action Required:**

```bash
# Check if your app supports 16 KB pages
./gradlew :app:check16KbPagesSupport

# Rebuild native libraries with 16 KB alignment
# In your native build configuration:
# CMakeLists.txt
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-z,max-page-size=16384")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-z,max-page-size=16384")
```

**Testing:**

```bash
# Test on 16 KB device
adb shell getprop ro.product.cpu.pagesize.max
# Should return: 16384

# Run your app and check for crashes
```

### ApplicationStartInfo API

**Purpose:** Detailed startup telemetry and diagnostics.

**Implementation:**

```kotlin
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.VANILLA_ICE_CREAM) {
            setupStartupMonitoring()
        }
    }
    
    @RequiresApi(Build.VERSION_CODES.VANILLA_ICE_CREAM)
    private fun setupStartupMonitoring() {
        val activityManager = getSystemService(ActivityManager::class.java)
        
        activityManager.addApplicationStartInfoCompletionListener(
            mainExecutor
        ) { startInfo ->
            logStartupMetrics(startInfo)
        }
    }
    
    @RequiresApi(Build.VERSION_CODES.VANILLA_ICE_CREAM)
    private fun logStartupMetrics(info: ApplicationStartInfo) {
        val metrics = mapOf(
            "startup_state" to info.startupState.toString(),
            "launch_mode" to info.launchMode.toString(),
            "timestamp" to info.startupTimestampMillis,
            "reason" to info.reason.toString(),
            "process_name" to info.processName
        )
        
        // Send to analytics
        analytics.logEvent("app_startup", metrics)
        
        // Log for debugging
        Log.d("Startup", """
            State: ${info.startupState}
            Launch Mode: ${info.launchMode}
            Reason: ${info.reason}
            Duration: ${System.currentTimeMillis() - info.startupTimestampMillis}ms
        """.trimIndent())
    }
}
```

**Startup States:**

```kotlin
when (startInfo.startupState) {
    ApplicationStartInfo.STARTUP_STATE_STARTED -> {
        // App process started
    }
    ApplicationStartInfo.STARTUP_STATE_FIRST_FRAME_DRAWN -> {
        // First frame rendered
    }
    ApplicationStartInfo.STARTUP_STATE_ERROR -> {
        // Startup failed
    }
}
```

**Launch Modes:**

```kotlin
when (startInfo.launchMode) {
    ApplicationStartInfo.START_TYPE_COLD -> {
        // Cold start - process created from scratch
    }
    ApplicationStartInfo.START_TYPE_WARM -> {
        // Warm start - process exists, activity recreated
    }
    ApplicationStartInfo.START_TYPE_HOT -> {
        // Hot start - process and activity exist
    }
}
```

### Foreground Service Restrictions

**Impact:** Background initialization strategies must adapt.

**Changes:**
- `BOOT_COMPLETED` receivers face stricter limits
- Data sync services limited to 6 hours per 24-hour period
- Exceeding limits causes `RemoteServiceException` crash

**Solution:**

```kotlin
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            // DON'T start foreground service immediately
            
            // Instead, schedule WorkManager
            val workRequest = OneTimeWorkRequestBuilder<InitWorker>()
                .setInitialDelay(5, TimeUnit.MINUTES)
                .build()
            
            WorkManager.getInstance(context).enqueue(workRequest)
        }
    }
}
```

### Edge-to-Edge Enforcement

**Impact:** UI layout changes may affect perceived startup time.

**Changes:**
- Apps targeting API 35 must handle edge-to-edge by default
- System bars are transparent
- Content draws behind status/navigation bars

**Solution:**

```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        
        setContent {
            AppTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    MainScreen(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}
```

## Android 16 (API 36)

### ProfilingManager API

**Purpose:** System-triggered profiling for field issues.

**Implementation:**

```kotlin
class MyApp : Application() {
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.VANILLA_ICE_CREAM) {
            setupProfilingTriggers()
        }
    }
    
    @RequiresApi(Build.VERSION_CODES.VANILLA_ICE_CREAM)
    private fun setupProfilingTriggers() {
        val profilingManager = getSystemService(ProfilingManager::class.java) ?: return
        
        // 1. Register a global listener to handle captured traces
        profilingManager.registerForAllProfilingResults(mainExecutor) { result ->
            val traceFile = File(result.path)
            uploadTraceForAnalysis(traceFile)
        }
        
        // 2. Define the triggers we want to capture
        val triggers = listOf(
            ProfilingTrigger.Builder(ProfilingTrigger.TRIGGER_TYPE_COLD_START).build(),
            ProfilingTrigger.Builder(ProfilingTrigger.TRIGGER_TYPE_ANR).build()
        )
        
        // 3. Register the triggers with the system
        profilingManager.addProfilingTriggers(triggers)
    }
    
    private fun uploadTraceForAnalysis(traceFile: File) {
        // Upload to your analytics/crash reporting service
        applicationScope.launch(Dispatchers.IO) {
            analyticsService.uploadTrace(traceFile)
        }
    }
}
```

**Benefits:**
- Automatic trace capture for slow startups in production
- No need to manually reproduce issues
- Real device data from actual users

### getStartComponent() API

**Purpose:** Identify which component triggered app start.

**Implementation:**

```kotlin
@RequiresApi(36)
fun optimizeBasedOnStartComponent(startInfo: ApplicationStartInfo) {
    val startComponent = startInfo.getStartComponent()
    
    when (startComponent) {
        ApplicationStartInfo.START_COMPONENT_ACTIVITY -> {
            // Started by an Activity (User launched from launcher or deep link)
            initializeFullApp()
        }
        ApplicationStartInfo.START_COMPONENT_SERVICE -> {
            // Started by a Service in background
            initializeMinimalForService()
        }
        ApplicationStartInfo.START_COMPONENT_BROADCAST -> {
            // Started by a Broadcast Receiver
            initializeMinimalForBroadcast()
        }
        ApplicationStartInfo.START_COMPONENT_CONTENT_PROVIDER -> {
            // Started by a Content Provider
            initializeMinimalForContentProvider()
        }
        else -> {
            // Unknown or other start component
            initializeMinimal()
        }
    }
}
```

### CPU/GPU Headroom APIs

**Purpose:** Adjust startup complexity based on device thermal state.

**Implementation:**

```kotlin
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        if (Build.VERSION.SDK_INT >= 36) {
            adjustStartupBasedOnHeadroom()
        }
    }
    
    @RequiresApi(36)
    private fun adjustStartupBasedOnHeadroom() {
        val healthManager = getSystemService(SystemHealthManager::class.java) ?: return
        
        val cpuParams = CpuHeadroomParams.Builder()
            .setDurationMillis(500)
            .setStatType(CpuHeadroomParams.CPU_HEADROOM_CALCULATION_TYPE_AVERAGE)
            .build()
        val gpuParams = GpuHeadroomParams.Builder()
            .setDurationMillis(500)
            .setStatType(GpuHeadroomParams.GPU_HEADROOM_CALCULATION_TYPE_AVERAGE)
            .build()

        val cpuHeadroom = healthManager.getCpuHeadroom(cpuParams)
        val gpuHeadroom = healthManager.getGpuHeadroom(gpuParams)
        
        // Headroom range is typically 0.0 to 100.0f (or 0.0 to 1.0f depending on platform scaling)
        val isLowCpu = if (cpuHeadroom > 1.0f) cpuHeadroom < 30.0f else cpuHeadroom < 0.3f
        val isModerateCpu = if (cpuHeadroom > 1.0f) cpuHeadroom < 60.0f else cpuHeadroom < 0.6f
        
        when {
            isLowCpu -> {
                // Device is hot/throttled
                Log.d("Startup", "Low CPU headroom ($cpuHeadroom) - minimal initialization")
                initializeMinimal()
                skipAnimations = true
            }
            isModerateCpu -> {
                // Moderate headroom
                Log.d("Startup", "Moderate CPU headroom ($cpuHeadroom) - standard initialization")
                initializeStandard()
            }
            else -> {
                // Plenty of headroom
                Log.d("Startup", "High CPU headroom ($cpuHeadroom) - full initialization")
                initializeFull()
                preloadOptionalFeatures()
            }
        }
    }
}
```

### Enhanced Background Restrictions

**Changes:**
- Stricter limits on background work
- More aggressive process killing
- Faster cache eviction

**Solution:**

```kotlin
// Use WorkManager for all background tasks
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        // Schedule periodic sync
        val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
            repeatInterval = 1,
            repeatIntervalTimeUnit = TimeUnit.HOURS
        )
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .setRequiresBatteryNotLow(true)
                    .build()
            )
            .build()
        
        WorkManager.getInstance(this)
            .enqueueUniquePeriodicWork(
                "sync",
                ExistingPeriodicWorkPolicy.KEEP,
                syncRequest
            )
    }
}
```

## Migration Checklist

### Android 15
- [ ] Test on 16 KB page size devices
- [ ] Rebuild native libraries with 16 KB alignment
- [ ] Implement ApplicationStartInfo telemetry
- [ ] Audit BOOT_COMPLETED receivers
- [ ] Migrate to WorkManager for background init
- [ ] Handle edge-to-edge UI
- [ ] Test foreground service limits

### Android 16
- [ ] Register ProfilingManager triggers
- [ ] Implement getStartComponent() optimization
- [ ] Use CPU/GPU headroom APIs
- [ ] Migrate all background work to WorkManager
- [ ] Test with aggressive process killing
- [ ] Update crash reporting for new exceptions

## Testing on New Platforms

### Emulator Setup

```bash
# Create Android 15 emulator with 16 KB pages
avdmanager create avd \
  -n "Android15_16KB" \
  -k "system-images;android-35;google_apis;x86_64" \
  -d "pixel_6"

# Start emulator
emulator -avd Android15_16KB
```

### Device Testing

```bash
# Check device page size
adb shell getprop ro.product.cpu.pagesize.max

# Monitor startup metrics
adb logcat | grep -E "ActivityManager|Startup"

# Capture system trace
adb shell perfetto -o /data/misc/perfetto-traces/trace -t 10s \
  sched freq idle am wm gfx view binder_driver hal dalvik
```

## Performance Expectations

### Android 15 (16 KB Pages)
- **Cold start**: 20-30% faster under memory pressure
- **Power consumption**: 4-5% lower during launch
- **Memory efficiency**: Better page utilization

### Android 16 (Headroom APIs)
- **Adaptive performance**: 10-20% improvement on throttled devices
- **Better UX**: Graceful degradation on hot devices
- **Field diagnostics**: Faster issue resolution with ProfilingManager

## Summary

**Android 15 Key Changes:**
- 16 KB page support (rebuild native code)
- ApplicationStartInfo API (telemetry)
- Stricter foreground service limits
- Edge-to-edge enforcement

**Android 16 Key Changes:**
- ProfilingManager (automatic traces)
- getStartComponent() (optimize by entry point)
- CPU/GPU headroom (adaptive initialization)
- Enhanced background restrictions

**Action Items:**
1. Test on Android 15+ devices
2. Implement new telemetry APIs
3. Adapt background initialization strategies
4. Use headroom APIs for adaptive performance
5. Monitor field performance with ProfilingManager
