# Startup Profiles (DEX Layout Optimization)

Startup Profiles optimize the physical layout of classes in DEX files to minimize disk I/O during app launch.

## The Problem

Android apps are packaged in DEX (Dalvik Executable) files. Large apps have multiple DEX files:
- `classes.dex` (primary)
- `classes2.dex` (secondary)
- `classes3.dex` (tertiary)
- etc.

**Issue:** If startup-critical classes are scattered across multiple DEX files, the system must:
1. Read from multiple files (slow disk I/O)
2. Handle page faults (memory management overhead)
3. Load classes in non-optimal order

**Result:** 200-500ms added to cold start time.

## The Solution

Startup Profiles tell R8 to group all startup-critical classes into the **primary DEX file** (`classes.dex`), ensuring sequential disk reads.

## Impact

- **15-30% faster startup** (on top of Baseline Profiles)
- **Reduced page faults** during class loading
- **Better memory locality**

## Setup

### 1. Enable in Build Configuration

```kotlin
// app/build.gradle.kts
android {
    buildTypes {
        release {
            isMinifyEnabled = true
            
            // Enable startup profile generation
            experimentalProperties["android.experimental.art-profile-r8-rewriting"] = true
        }
    }
}
```

### 2. Generate Startup Profile

```kotlin
// baselineprofile/src/main/java/StartupProfileGenerator.kt
@RunWith(AndroidJUnit4::class)
class StartupProfileGenerator {
    
    @get:Rule
    val rule = BaselineProfileRule()
    
    @Test
    fun generateStartupProfile() = rule.collect(
        packageName = "com.example.myapp",
        maxIterations = 15,
        stableIterations = 3,
        includeInStartupProfile = true // Key flag!
    ) {
        // Only navigate the CRITICAL startup path
        pressHome()
        startActivityAndWait()
        
        // Wait for first screen to fully load
        device.wait(Until.hasObject(By.text("Home")), 5000)
        
        // DO NOT navigate to other screens
        // Startup profile should only include first screen
    }
}
```

### 3. Generate Profile

```bash
./gradlew :baselineprofile:pixel6Api33BenchmarkAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.androidx.benchmark.enabledRules=BaselineProfile

# Profile saved to: app/src/main/startup-prof.txt
```

## Profile Format

```text
# startup-prof.txt
# Classes needed for startup (no method signatures)
Lcom/example/myapp/MyApplication;
Lcom/example/myapp/MainActivity;
Lcom/example/myapp/ui/HomeScreenKt;
Lcom/example/myapp/ui/theme/ThemeKt;
Lcom/example/myapp/di/AppModule;
Lcom/example/myapp/viewmodel/MainViewModel;
```

**Key Difference from Baseline Profiles:**
- **Baseline Profile**: Classes + Methods (for AOT compilation)
- **Startup Profile**: Classes only (for DEX layout)

## Verify DEX Layout

### Check Primary DEX Size

```bash
# Extract APK
unzip app-release.apk -d extracted/

# Check DEX file sizes
ls -lh extracted/classes*.dex

# Analyze primary DEX contents
dexdump -f extracted/classes.dex | grep "Class descriptor"
```

### Ensure Startup Classes in Primary DEX

```bash
# Check if MainActivity is in primary DEX
dexdump -f extracted/classes.dex | grep "MainActivity"

# Should appear in classes.dex, not classes2.dex
```

## Best Practices

### 1. Keep Startup Profile Minimal

**Only include the absolute minimum for first screen:**

```kotlin
// GOOD: Minimal startup path
@Test
fun generateStartupProfile() = rule.collect(...) {
    startActivityAndWait()
    // Stop here - first screen only
}

// BAD: Too much navigation
@Test
fun generateStartupProfile() = rule.collect(...) {
    startActivityAndWait()
    device.findObject(By.text("Profile")).click() // Don't do this
    device.findObject(By.text("Settings")).click() // Don't do this
}
```

### 2. Stay Under Primary DEX Limit

Primary DEX has a size limit (~64K methods). If your startup profile is too large:

**Symptom:** Classes overflow into `classes2.dex`

**Solution:** Reduce startup profile scope

```kotlin
// Audit your startup path
@Test
fun auditStartupClasses() {
    // Use Perfetto to see which classes are actually loaded
    // Remove non-essential classes from profile
}
```

### 3. Combine with Baseline Profiles

**Optimal setup:**
- **Baseline Profile**: AOT compile startup + frequent paths
- **Startup Profile**: DEX layout for startup only

```kotlin
@Test
fun generateBothProfiles() = rule.collect(
    packageName = "com.example.myapp",
    includeInStartupProfile = true // Generates both!
) {
    // Startup path
    startActivityAndWait()
    device.wait(Until.hasObject(By.text("Home")), 5000)
    
    // Additional paths for Baseline Profile only
    // (won't affect Startup Profile)
    device.findObject(By.text("Profile")).click()
    device.waitForIdle()
}
```

## Manual Startup Profile

If automatic generation doesn't work, create manually:

```text
# app/src/main/startup-prof.txt

# Application class
Lcom/example/myapp/MyApplication;

# Main activity
Lcom/example/myapp/MainActivity;

# Dependency injection
Lcom/example/myapp/di/AppModule;
Lcom/example/myapp/di/AppComponent;

# First screen composables
Lcom/example/myapp/ui/HomeScreenKt;
Lcom/example/myapp/ui/theme/ThemeKt;
Lcom/example/myapp/ui/theme/ColorKt;
Lcom/example/myapp/ui/theme/TypeKt;

# ViewModels for first screen
Lcom/example/myapp/viewmodel/MainViewModel;

# Critical data layer
Lcom/example/myapp/data/Repository;
Lcom/example/myapp/data/local/Database;
```

## Measure Impact

### Before/After Benchmark

```kotlin
@Test
fun startupWithoutStartupProfile() {
    // Build without startup profile
    benchmarkRule.measureRepeated(
        packageName = "com.example.myapp",
        metrics = listOf(StartupTimingMetric()),
        iterations = 10
    ) {
        startActivityAndWait()
    }
}

@Test
fun startupWithStartupProfile() {
    // Build with startup profile
    benchmarkRule.measureRepeated(
        packageName = "com.example.myapp",
        metrics = listOf(StartupTimingMetric()),
        iterations = 10
    ) {
        startActivityAndWait()
    }
}
```

### Expected Results

- **Without Startup Profile**: 2.5s cold start
- **With Startup Profile**: 2.1s cold start (15% improvement)

## Common Issues

### Profile Not Applied

**Symptom:** No performance improvement

**Causes:**
1. Profile file not in APK
2. R8 not rewriting profile
3. Startup classes already in primary DEX

**Solution:**
```bash
# Verify profile in APK
unzip -l app-release.apk | grep startup
# Should show: assets/dexopt/startup.prof

# Check R8 logs
./gradlew :app:assembleRelease --info | grep "startup"
```

### Primary DEX Overflow

**Symptom:** Build warning about DEX method limit

**Solution:** Reduce startup profile scope

```text
# Remove non-critical classes
# Keep only:
# - Application
# - MainActivity
# - First screen composables
# - Essential ViewModels
```

### Conflicts with Multidex

**Symptom:** App crashes on API < 21

**Solution:** Ensure multidex is properly configured

```kotlin
// app/build.gradle.kts
android {
    defaultConfig {
        multiDexEnabled = true
    }
}

dependencies {
    implementation("androidx.multidex:multidex:2.0.1")
}
```

## Integration with CI/CD

```yaml
# .github/workflows/profiles.yml
name: Generate Profiles

on:
  push:
    branches: [ main ]

jobs:
  generate:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Generate profiles
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          script: |
            ./gradlew :baselineprofile:pixel6Api33BenchmarkAndroidTest
            
      - name: Commit profiles
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add app/src/main/baseline-prof.txt
          git add app/src/main/startup-prof.txt
          git commit -m "Update profiles" || echo "No changes"
          git push
```

## Summary

**Startup Profiles optimize DEX layout for faster class loading:**

1. **Generate** with `includeInStartupProfile = true`
2. **Keep minimal** - first screen only
3. **Verify** in APK with dexdump
4. **Measure** with Macrobenchmark
5. **Combine** with Baseline Profiles for maximum impact

**Expected improvement: 15-30% faster startup**

**Best used with:**
- Baseline Profiles (AOT compilation)
- R8 Full Mode (code optimization)
- App Startup Library (initialization consolidation)
