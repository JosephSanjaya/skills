# Koin Gradle Setup

## libs.versions.toml

Ensure version alignment between `koin-core` and `koin-annotations`:

```toml
[versions]
kotlin = "2.3.20"
koin = "4.2.0"
koin-plugin = "1.0.0-RC2"

[libraries]
koin-core = { module = "io.insert-koin:koin-core", version.ref = "koin" }
koin-annotations = { module = "io.insert-koin:koin-annotations", version.ref = "koin" }
koin-core-viewmodel = { module = "io.insert-koin:koin-core-viewmodel", version.ref = "koin" }
koin-android-workmanager = { module = "io.insert-koin:koin-android-workmanager", version.ref = "koin" }

[plugins]
koin-compiler = { id = "io.insert-koin.compiler.plugin", version.ref = "koin-plugin" }
```

## settings.gradle.kts

Make sure plugin repositories are properly set up:

```kotlin
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
```

## Standard Android/JVM Module Build Configuration

```kotlin
plugins {
    alias(libs.plugins.koin.compiler)
}

dependencies {
    implementation(libs.koin.core)
    implementation(libs.koin.annotations)
    
    // Required if @KoinViewModel is used (fails compiler validation otherwise):
    implementation(libs.koin.core.viewmodel)
    
    // Required if @KoinWorker is used:
    implementation(libs.koin.android.workmanager)
}
```

## Kotlin Multiplatform (KMP) Module Configuration

The Koin compiler plugin handles KMP setup automatically without complex manual source set task wiring:

```kotlin
plugins {
    kotlin("multiplatform")
    alias(libs.plugins.koin.compiler)
}

kotlin {
    androidTarget()
    jvm()
    iosX64()
    iosArm64()
    iosSimulatorArm64()

    sourceSets {
        commonMain.dependencies {
            implementation(libs.koin.core)
            implementation(libs.koin.annotations)
        }
    }
}
```

## Aggregator App Module Configuration

Configure the plugin options in your final composition root (typically the aggregator `app` module):

```kotlin
// build.gradle.kts (app module only)
koinCompiler {
    compileSafety = true       // Enable compile-time validation checks (default: true)
    userLogs = true            // Show component discovery logs during builds
    skipDefaultValues = true   // Skip validation of parameters with default arguments
}
```

### Note on Incremental Compilation (IC) Catch-22:
When internal lambda bodies or dependency declarations (e.g. `single<Repository>()`) are modified, the public class signatures/ABI do not change. As a result, Kotlin Incremental Compilation (IC) may flag the aggregator module as up-to-date and skip recompilation, preventing the compiler plugin from assembling and validating the full A3 graph. This leads to silent runtime `NoDefinitionFoundException` crashes.

**Workarounds**:
- Disable Kotlin incremental compilation in `gradle.properties`:
  ```properties
  kotlin.incremental.multiplatform=false
  # or
  kotlin.incremental=false
  ```
- Run a clean build when changes to DI declarations do not trigger downstream compilation:
  ```bash
  ./gradlew clean assembleDebug
  ```

## Koin Compiler Plugin Options Reference

| Option | Default | Description |
|---|---|---|
| `compileSafety` | `true` | Enables compile-time dependency graph validation checks (A2/A3/A4). |
| `userLogs` | `false` | Enables printing discovered dependencies during the compilation phase. |
| `debugLogs` | `false` | Enables verbose internal debugging logs for the compiler plugin. |
| `unsafeDslChecks` / `dslSafetyChecks` | `true` | Enforces `create(::T)` as the sole instruction inside provider lambdas. |
| `skipDefaultValues` | `true` | Skips dependency checking for parameters with defined default arguments. |
