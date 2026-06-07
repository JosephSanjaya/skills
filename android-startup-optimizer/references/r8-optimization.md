# R8 Optimization

R8 is Android's code shrinker, obfuscator, and optimizer. Proper configuration can improve startup by 30-40%.

## Enable R8 Full Mode

```kotlin
// gradle.properties
android.enableR8.fullMode=true
```

## Basic Configuration

```kotlin
// app/build.gradle.kts
android {
    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

## ProGuard Rules

```proguard
# proguard-rules.pro

# Keep application class
-keep class com.example.myapp.MyApplication { *; }

# Keep Parcelable implementations
-keepclassmembers class * implements android.os.Parcelable {
    public static final ** CREATOR;
}

# Keep serializable classes
-keepclassmembers class * implements java.io.Serializable {
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}

# Kotlin serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt

# Compose
-keep class androidx.compose.** { *; }
-keep @androidx.compose.runtime.Stable class * { *; }

# Retrofit
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**

# Baseline Profiles - R8 automatically rewrites these
-keepattributes SourceFile,LineNumberTable
```

## Optimization Strategies

### Method Inlining

R8 automatically inlines small methods to reduce call overhead:

```kotlin
// Before R8
fun calculateTotal(price: Double, tax: Double): Double {
    return addTax(price, tax)
}

fun addTax(price: Double, tax: Double): Double {
    return price + (price * tax)
}

// After R8 (inlined)
fun calculateTotal(price: Double, tax: Double): Double {
    return price + (price * tax)
}
```

### Class Merging

R8 merges classes that are only used together:

```kotlin
// Before R8
class UserData(val name: String)
class UserMetadata(val id: String)

// After R8 (merged into single class)
class User(val name: String, val id: String)
```

### Dead Code Elimination

```kotlin
// Before R8
object FeatureFlags {
    const val FEATURE_A = true
    const val FEATURE_B = false
    const val FEATURE_C = true
}

fun initializeFeatures() {
    if (FeatureFlags.FEATURE_A) {
        initFeatureA() // Kept
    }
    if (FeatureFlags.FEATURE_B) {
        initFeatureB() // Removed - never executed
    }
    if (FeatureFlags.FEATURE_C) {
        initFeatureC() // Kept
    }
}

// After R8
fun initializeFeatures() {
    initFeatureA()
    initFeatureC()
}
```

## Verify Optimization

### Check APK Size

```bash
# Before optimization
./gradlew :app:assembleDebug
ls -lh app/build/outputs/apk/debug/app-debug.apk

# After optimization
./gradlew :app:assembleRelease
ls -lh app/build/outputs/apk/release/app-release.apk
```

### Analyze APK

```bash
# Android Studio: Build → Analyze APK
# Or command line:
apkanalyzer dex packages app-release.apk
apkanalyzer dex code --class com.example.MyClass app-release.apk
```

### Mapping File

R8 generates a mapping file for deobfuscation:

```
# app/build/outputs/mapping/release/mapping.txt
com.example.myapp.MainActivity -> a.b.c:
    void onCreate(android.os.Bundle) -> a
    void onResume() -> b
```

Upload to Play Console for crash deobfuscation.

## Common Issues

### Missing Classes at Runtime

**Symptom:** `ClassNotFoundException` or `NoSuchMethodException`

**Solution:** Add keep rules

```proguard
# Keep specific class
-keep class com.example.ReflectedClass { *; }

# Keep all classes in package
-keep class com.example.reflection.** { *; }

# Keep methods with specific annotation
-keepclassmembers class * {
    @com.example.KeepThis *;
}
```

### Baseline Profile Not Applied

**Symptom:** No performance improvement after adding profiles

**Solution:** R8 automatically rewrites profiles. Verify in APK:

```bash
unzip -l app-release.apk | grep baseline
# Should show: assets/dexopt/baseline.prof
```

### Over-Aggressive Optimization

**Symptom:** App crashes or behaves incorrectly

**Solution:** Disable specific optimizations

```proguard
# Disable optimization for specific package
-keep,allowoptimization class com.example.problematic.** { *; }

# Disable all optimizations (not recommended)
-dontoptimize
```

## Advanced: Custom Optimization

### Aggressive Shrinking

```proguard
# Remove logging in release
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# Remove debug code
-assumenosideeffects class kotlin.jvm.internal.Intrinsics {
    public static void checkParameterIsNotNull(...);
    public static void checkNotNullParameter(...);
}
```

### Optimize Enums

```proguard
# Convert enums to integers
-optimizations !code/simplification/enum
```

## Measure Impact

### Before/After Comparison

```kotlin
// Macrobenchmark test
@Test
fun startupWithR8() {
    benchmarkRule.measureRepeated(
        packageName = "com.example.myapp",
        metrics = listOf(
            StartupTimingMetric(),
            TraceSectionMetric("ActivityStart")
        ),
        iterations = 10,
        startupMode = StartupMode.COLD
    ) {
        startActivityAndWait()
    }
}
```

### APK Size Reduction

Typical results:
- **Code size**: 30-50% reduction
- **Resource size**: 20-30% reduction (with shrinkResources)
- **Total APK**: 25-40% smaller

### Startup Improvement

Reddit case study: **40% faster cold startup** after enabling R8 full mode.

## Integration with Profiles

R8 works seamlessly with Baseline Profiles:

1. Generate Baseline Profile (human-readable class names)
2. R8 obfuscates code during release build
3. R8 automatically rewrites profile with obfuscated names
4. Profile embedded in APK with correct references

**No manual intervention needed!**

## Best Practices

1. **Always enable in release builds** - Never ship debug builds
2. **Test thoroughly** - R8 can break reflection-heavy code
3. **Keep mapping files** - Essential for crash deobfuscation
4. **Use -keepattributes** - Preserve debugging info
5. **Monitor APK size** - Track size over time
6. **Combine with profiles** - R8 + Baseline Profiles = maximum performance
7. **Update regularly** - Newer R8 versions have better optimizations

## Troubleshooting

### Enable R8 Logging

```kotlin
// gradle.properties
android.enableR8.fullMode=true
android.r8.failOnMissingClasses=false
```

### Generate Full Report

```bash
./gradlew :app:assembleRelease --info > r8-log.txt
```

### Test Obfuscated Build

```bash
# Install release build on device
./gradlew :app:installRelease

# Run and check for crashes
adb logcat | grep -i exception
```

## Summary

R8 optimization is **essential** for production apps:
- Reduces APK size by 25-40%
- Improves startup by 30-40%
- Works automatically with Baseline Profiles
- Minimal configuration required

**Always enable R8 full mode for release builds.**
