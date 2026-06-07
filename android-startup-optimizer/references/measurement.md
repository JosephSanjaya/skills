# Measurement and Profiling

## Macrobenchmark Setup

### 1. Add Benchmark Module

```kotlin
// benchmark/build.gradle.kts
plugins {
    id("com.android.test")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.benchmark"
    compileSdk = 34
    
    defaultConfig {
        minSdk = 23
        targetSdk = 34
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    
    targetProjectPath = ":app"
    experimentalProperties["android.experimental.self-instrumenting"] = true
}

dependencies {
    implementation("androidx.benchmark:benchmark-macro-junit4:1.2.4")
    implementation("androidx.test.ext:junit:1.1.5")
    implementation("androidx.test.espresso:espresso-core:3.5.1")
    implementation("androidx.test.uiautomator:uiautomator:2.3.0")
}
```

### 2. Create Startup Benchmark

```kotlin
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()
    
    @Test
    fun startupCompilationNone() = startup(CompilationMode.None())
    
    @Test
    fun startupCompilationBaselineProfile() = 
        startup(CompilationMode.Partial(BaselineProfileMode.Require))
    
    private fun startup(compilationMode: CompilationMode) = 
        benchmarkRule.measureRepeated(
            packageName = "com.example.myapp",
            metrics = listOf(
                StartupTimingMetric(),
                FrameTimingMetric()
            ),
            compilationMode = compilationMode,
            iterations = 10,
            startupMode = StartupMode.COLD,
            setupBlock = {
                pressHome()
            }
        ) {
            startActivityAndWait()
        }
}
```

### 3. Run and Analyze

```bash
# Run benchmark
./gradlew :benchmark:connectedCheck

# Results location
benchmark/build/outputs/connected_android_test_additional_output/
```

## Perfetto Tracing

### Capture System Trace

```kotlin
// In your test or debug build
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // Start tracing
        if (BuildConfig.DEBUG) {
            Trace.beginSection("MainActivity.onCreate")
        }
        
        super.onCreate(savedInstanceState)
        
        // Your initialization code
        
        if (BuildConfig.DEBUG) {
            Trace.endSection()
        }
    }
}
```

### Analyze in Perfetto

1. Capture trace: `adb shell perfetto -o /data/misc/perfetto-traces/trace -t 10s sched freq idle am wm gfx view binder_driver hal dalvik camera input res memory`
2. Pull trace: `adb pull /data/misc/perfetto-traces/trace .`
3. Open at https://ui.perfetto.dev

### What to Look For

- **Orange bars**: Main thread blocked (uninterruptible sleep)
- **Binder transactions**: Cross-process calls
- **GC events**: Excessive garbage collection
- **Layout inflation**: View hierarchy creation
- **Class loading**: DEX file reads

## Android Vitals Integration

### Enable Play Console Reporting

```kotlin
// AndroidManifest.xml
<application>
    <meta-data
        android:name="com.google.android.gms.version"
        android:value="@integer/google_play_services_version" />
</application>
```

### Custom Telemetry (Android 15+)

```kotlin
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.VANILLA_ICE_CREAM) {
            val activityManager = getSystemService(ActivityManager::class.java)
            
            activityManager.addApplicationStartInfoCompletionListener(
                mainExecutor
            ) { startInfo ->
                // Log startup metrics
                Log.d("Startup", """
                    Reason: ${startInfo.startupState}
                    Timestamp: ${startInfo.startupTimestampMillis}
                    Launch Mode: ${startInfo.launchMode}
                """.trimIndent())
                
                // Send to analytics
                analytics.logStartup(
                    duration = System.currentTimeMillis() - startInfo.startupTimestampMillis,
                    reason = startInfo.startupState.toString()
                )
            }
        }
    }
}
```

## StrictMode for Development

```kotlin
class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        
        if (BuildConfig.DEBUG) {
            StrictMode.setThreadPolicy(
                StrictMode.ThreadPolicy.Builder()
                    .detectDiskReads()
                    .detectDiskWrites()
                    .detectNetwork()
                    .penaltyLog()
                    .penaltyDeath() // Crash on violation
                    .build()
            )
            
            StrictMode.setVmPolicy(
                StrictMode.VmPolicy.Builder()
                    .detectLeakedSqlLiteObjects()
                    .detectLeakedClosableObjects()
                    .penaltyLog()
                    .build()
            )
        }
    }
}
```

## reportFullyDrawn() for TTFD

```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            var dataLoaded by remember { mutableStateOf(false) }
            
            LaunchedEffect(Unit) {
                // Load critical data
                loadInitialData()
                dataLoaded = true
                
                // Report when fully interactive
                reportFullyDrawn()
            }
            
            if (dataLoaded) {
                MainScreen()
            } else {
                LoadingScreen()
            }
        }
    }
}
```

## CI/CD Integration

```yaml
# .github/workflows/benchmark.yml
name: Startup Benchmark

on:
  pull_request:
    branches: [ main ]

jobs:
  benchmark:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up JDK
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          
      - name: Run benchmarks
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          script: ./gradlew :benchmark:connectedCheck
          
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark/build/outputs/
```

## Key Metrics to Track

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Cold Start (p50) | < 2.0s | 2.0-3.5s | > 3.5s |
| Cold Start (p90) | < 3.5s | 3.5-5.0s | > 5.0s |
| TTID | < 1.5s | 1.5-2.5s | > 2.5s |
| TTFD | < 2.5s | 2.5-4.0s | > 4.0s |
| Frame drops (0-5s) | < 5 | 5-10 | > 10 |
| Main thread block | < 100ms | 100-300ms | > 300ms |
