# Baseline Profiles

Baseline Profiles tell ART which classes and methods to pre-compile (AOT) during app installation, eliminating JIT warmup time.

## Impact

- **30-40% faster startup** (Meta, Duolingo)
- **Reduced JIT thread activity** (25% → 3%)
- **Immediate performance** on first launch after install

## Setup

### 1. Add Dependencies

```kotlin
// app/build.gradle.kts
plugins {
    id("androidx.baselineprofile")
}

dependencies {
    baselineProfile(project(":baselineprofile"))
}

// baselineprofile/build.gradle.kts
plugins {
    id("com.android.test")
    id("androidx.baselineprofile")
}

android {
    targetProjectPath = ":app"
}

dependencies {
    implementation("androidx.benchmark:benchmark-macro-junit4:1.2.4")
}
```

### 2. Generate Profile

```kotlin
// baselineprofile/src/main/java/BaselineProfileGenerator.kt
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {
    
    @get:Rule
    val rule = BaselineProfileRule()
    
    @Test
    fun generate() = rule.collect(
        packageName = "com.example.myapp",
        maxIterations = 15,
        stableIterations = 3
    ) {
        // Cold start
        pressHome()
        startActivityAndWait()
        
        // Navigate critical paths
        device.findObject(By.text("Home")).click()
        device.waitForIdle()
        
        device.findObject(By.text("Profile")).click()
        device.waitForIdle()
        
        device.findObject(By.text("Settings")).click()
        device.waitForIdle()
    }
}
```

### 3. Generate and Build

```bash
# Generate profile
./gradlew :baselineprofile:pixel6Api33BenchmarkAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.androidx.benchmark.enabledRules=BaselineProfile

# Profile saved to: app/src/main/baseline-prof.txt

# Build release with profile
./gradlew :app:assembleRelease
```

## Validate Profile

### Check APK Contents

```bash
# Extract APK
unzip app-release.apk -d extracted/

# Check for compiled profile
ls extracted/assets/dexopt/baseline.prof
ls extracted/assets/dexopt/baseline.profm
```

### Verify in Android Studio

1. Build → Analyze APK
2. Navigate to `assets/dexopt/`
3. Confirm `baseline.prof` and `baseline.profm` exist

### Benchmark Comparison

```kotlin
@Test
fun startupNoProfile() = startup(CompilationMode.None())

@Test
fun startupWithProfile() = startup(
    CompilationMode.Partial(BaselineProfileMode.Require)
)

private fun startup(mode: CompilationMode) {
    benchmarkRule.measureRepeated(
        packageName = "com.example.myapp",
        metrics = listOf(StartupTimingMetric()),
        compilationMode = mode,
        iterations = 10,
        startupMode = StartupMode.COLD
    ) {
        startActivityAndWait()
    }
}
```

## Profile Format

```text
# Human-readable format (baseline-prof.txt)
Lcom/example/myapp/MainActivity;
Lcom/example/myapp/ui/HomeScreen;->HomeScreen(Landroidx/compose/runtime/Composer;I)V
Lcom/example/myapp/data/Repository;-><init>()V
Lcom/example/myapp/viewmodel/MainViewModel;->loadData()V
```

### Profile Rules

- `Lcom/example/Class;` - Entire class
- `Lcom/example/Class;->method()V` - Specific method
- `Lcom/example/Class;->method(Ljava/lang/String;)I` - Method with signature

## Advanced: Manual Profile Creation

```text
# Include all startup-critical classes
Lcom/example/myapp/MyApplication;
Lcom/example/myapp/MainActivity;
Lcom/example/myapp/di/AppModule;

# Include ViewModel initialization
Lcom/example/myapp/viewmodel/MainViewModel;-><init>(Lcom/example/myapp/data/Repository;)V
Lcom/example/myapp/viewmodel/MainViewModel;->loadInitialData()V

# Include Compose functions
Lcom/example/myapp/ui/HomeScreenKt;->HomeScreen(Landroidx/compose/runtime/Composer;I)V
Lcom/example/myapp/ui/theme/ThemeKt;->AppTheme(ZLkotlin/jvm/functions/Function2;Landroidx/compose/runtime/Composer;II)V

# Include critical data layer
Lcom/example/myapp/data/local/Database;
Lcom/example/myapp/data/remote/ApiService;
```

## Cloud Profiles (Google Play)

Google Play automatically generates profiles from real user behavior:

- Collected from opted-in users
- Updated periodically
- Merged with your supplied profile
- Reset on app updates (weekly updates lose benefit)

**Best practice**: Always ship developer-supplied profiles for consistent performance.

## Common Issues

### Profile Not Applied

**Symptom**: No performance improvement

**Causes**:
1. Profile file missing from APK
2. R8 minification broke class names
3. Profile rules don't match obfuscated names

**Solution**:
```kotlin
// Ensure R8 rewrites profile
android {
    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### Profile Too Large

**Symptom**: APK size increased significantly

**Solution**: Focus on startup-critical paths only. Remove rarely-used features from profile generation.

### Third-Party Library Compression

**Symptom**: Profile silently ignored (Duolingo case)

**Solution**: Check build logs for warnings. Verify profile files aren't compressed:

```kotlin
android {
    packagingOptions {
        jniLibs {
            useLegacyPackaging = false
        }
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}
```

## Maintenance

### Update Profile on Major Changes

Regenerate when:
- Adding new startup screens
- Changing navigation structure
- Refactoring critical paths
- Major dependency updates

### Monitor Profile Effectiveness

```kotlin
// Log JIT compilation events
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
    Debug.startMethodTracing("startup")
    // ... startup code ...
    Debug.stopMethodTracing()
}
```

## Integration with Startup Profiles

Baseline Profiles (code execution) + Startup Profiles (DEX layout) = Maximum performance

```kotlin
// Generate both
./gradlew :baselineprofile:pixel6Api33BenchmarkAndroidTest
./gradlew :app:generateReleaseStartupProfile
```

See [startup-profiles.md](startup-profiles.md) for DEX layout optimization.
