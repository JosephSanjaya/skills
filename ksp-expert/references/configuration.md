# KSP Configuration & Setup

## Gradle Configuration

### Plugin Setup
```kotlin
// settings.gradle.kts
pluginManagement {
    repositories {
        gradlePluginPortal()
    }
}

// build.gradle.kts (JVM/Android)
plugins {
    kotlin("jvm") version "2.4.0"
    id("com.google.devtools.ksp") version "2.3.9"
}

dependencies {
    // Add processor to KSP classpath (not compile classpath!)
    ksp("com.example:my-processor:1.0")
}
```

### Multiplatform (KMP) Setup
- **Avoid** global `ksp("...")` in KMP. Causes performance issues.
- **Do**: Target-specific configuration:
```kotlin
kotlin {
    jvm()
    androidTarget()
    iosArm64()
    iosSimulatorArm64()
}

dependencies {
    // Target common metadata (runs during common metadata compilation)
    add("kspCommonMainMetadata", project(":my-processor"))
    // Target JVM
    add("kspJvm", project(":my-processor"))
    // Target Android
    add("kspAndroid", project(":my-processor"))
    // Target iOS Arm64
    add("kspIosArm64", project(":my-processor"))
}
```

## Gradle Properties (`gradle.properties`)

- `ksp.useKSP2=true`: Enable KSP2.
- `org.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=1g`: Heap size for Gradle daemon (KSP2 runs here).
- `ksp.incremental.log=true`: Log dirty-set decisions. Outputs to build dir.
- `ksp.incremental.intermodule=false`: Disable intermodule tracking to prevent broad invalidations.

## Command Line Interface (CLI)

`KSPJvmMain` class in `symbol-processing-aa.jar`. Runs KSP2 standalone.

```bash
java -cp "symbol-processing-aa.jar:kotlin-stdlib.jar:kotlinx-coroutines-core.jar" \
  com.google.devtools.ksp.cmdline.KSPJvmMain \
  -jvm-target 17 \
  -module-name=main \
  -source-roots src/main/kotlin \
  -project-base-dir . \
  -output-base-dir=build/ksp/ \
  -caches-dir=build/ksp-caches/ \
  -class-output-dir=build/ksp-classes/ \
  -kotlin-output-dir=build/ksp-generated/kotlin/ \
  -resource-output-dir=build/ksp-generated/resources/ \
  -language-version=2.0 \
  -api-version=2.0 \
  -libraries=lib/dep1.jar:lib/dep2.jar \
  -jdk-home=/path/to/jdk \
  path/to/processor.jar
```

## Debugging

- **KSP2 Debugging**: Runs in Gradle daemon. Pass system property:
  ```bash
  ./gradlew assemble -Dorg.gradle.debug=true
  ```
- **Logging Level**: `-Dksp.logging=debug` (valid levels: `error`, `warn` / `warning`, `info`, `debug`).
