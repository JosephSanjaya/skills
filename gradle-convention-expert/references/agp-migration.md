# AGP 9.0+ Compatibility & Upgrades

## Core Requirements & Baselines

Upgrading custom convention plugins for AGP 9.x/Gradle 9.x baselines requires:
* **Gradle Toolchain Target:** Gradle 9.1.0 minimum (Gradle 9.4.1+ recommended for AGP 9.2+).
* **Java Toolchain Target:** Java 17 minimum. All project module compilation configurations must baseline to JDK 17.
* **Kotlin Compiler (KGP) Baseline:** AGP 9.0 relies on KGP 2.2.10+ compiler runtimes.

---

## Key AGP 9.0 Behavior Changes

1. **Built-in Kotlin Support (`android.builtInKotlin=true`)**:
   - AGP 9.0 compiles Kotlin natively. The `org.jetbrains.kotlin.android` plugin is incompatible and must be **removed** from build scripts.
   - For Java-only modules, disable Kotlin compilation via `android { enableKotlin = false }`.
2. **Strict new DSL (`android.newDsl=true`)**:
   - Legacy accessors such as `applicationVariants` have been removed. Use `androidComponents.onVariants` instead.
3. **Strict Package Names (`android.uniquePackageNames=true`)**:
   - Package/namespaces for Android libraries must be unique across all modules.

---

## 4 API Migration Targets

Ensure convention plugins replace the following deprecated/removed AGP 8.x endpoints:

| Deprecated/Removed API (AGP 8.x) | Modern Replacement (AGP 9.0+) | Details |
|---|---|---|
| `AndroidComponentsExtension.finalizeDSl` | `finalizeDsl` | Configuration DSL Hook |
| `Component.transformClassesWith` | `Instrumentation.transformClassesWith` | Bytecode Instrumentation API |
| `VariantBuilder.unitTestEnabled` | `enableUnitTest` (property on `VariantBuilder`) | Test Framework Configuration |
| `ProductFlavor.setDimension` | `dimension` (property assignment) | Build Flavor Configuration |

---

## Migrated Convention Blueprints

### 1. Composable Android Library Script Plugin (AGP 9.0+)
```kotlin
// build-logic/convention/src/main/kotlin/my.android.library.gradle.kts
plugins {
    id("com.android.library")
    // Do NOT apply "org.jetbrains.kotlin.android" (disallowed in AGP 9.0+)
}

android {
    compileSdk = 35

    defaultConfig {
        minSdk = 26
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

// Configure Kotlin compiler options via built-in Kotlin extension
kotlin {
    compilerOptions {
        languageVersion.set(org.jetbrains.kotlin.gradle.dsl.KotlinVersion.KOTLIN_2_0)
        // jvmTarget is auto-configured from compileOptions.targetCompatibility
    }
}
```

### 2. Composable Android Library Script Plugin (AGP 8.x Legacy Compatibility)
If your project is still on AGP 8.x and has `android.builtInKotlin=false` in `gradle.properties`:
```kotlin
// build-logic/convention/src/main/kotlin/my.android.library.gradle.kts
plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
}

android {
    compileSdk = 35

    defaultConfig {
        minSdk = 26
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}
```

### Downstream Application Consumer
Apply clean and declarative module-specific setups:
```kotlin
// app/build.gradle.kts
plugins {
    id("my.android.library")
}

dependencies {
    implementation(libs.androidx.appcompat)
}
```
