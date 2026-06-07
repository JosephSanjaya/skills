# Gradle Compilation & Performance Optimization

## Compile-Time snapshotting & Caches (Gradle 9.x / Kotlin 2.2)

Gradle 9.x optimizes compilation loops by employing:
* **Script Recompilation Avoidance:** Classpath snapshots generated at member level. If changes only affect internal task actions (non-ABI modifications), script recompilation is completely bypassed.
* **Pre-compiled Extensions:** Kotlin extensions for the Gradle API are distributed pre-compiled. Shaves up to 4 seconds off cold build runs on developer machines.
* **Strict Classpath Snapshots:** Class ABI signatures stored in cache. Incremental compilation tasks skipped entirely if signature matches.

---

## Configuration Cache Best Practices

Configuration cache serializes project task graphs and bypasses evaluation on subsequent runs. Enforce strict configuration-time rules:

1. **Avoid Eager Configuration:** Never use `tasks.create()`. Force lazy evaluation with `tasks.register()`:
   ```kotlin
   // Yes:
   tasks.register<CustomTask>("customTask")
   ```
2. **Prevent Mutable Project Reference Leaks:** Do not reference the `Project` instance inside task actions (`doFirst`/`doLast`). Capturing `Project` breaks task serialization:
   ```kotlin
   // No:
   tasks.register("brokenTask") {
       doLast {
           println(project.name) // Mutable leak
       }
   }

   // Yes:
   tasks.register("correctTask") {
       val projName = project.name // Resolve at configuration time
       doLast {
           println(projName)
       }
   }
   ```
3. **Avoid Imperative Configuration I/O:** Wrapping environments/process executions dynamically halts configuration cache. Wrap them lazily:
   ```kotlin
   // No:
   val branch = Runtime.getRuntime().exec("git rev-parse --abbrev-ref HEAD").inputStream.bufferedReader().readLine()

   // Yes:
   val branchProvider = providers.exec {
       commandLine("git", "rev-parse", "--abbrev-ref", "HEAD")
   }
   ```
4. **Configuration Cache Encryption Security:** Gradle 8.1+ encrypts the configuration cache with a machine-specific secret. 
   > [!IMPORTANT]
   > Never commit `.gradle/configuration-cache/` directory to source control or public CI build artifacts.

---

## Build Cache Determinism (UTF-8)

Enforce strict output determinism to avoid cache invalidation across different machines/OS:
```properties
# gradle.properties
org.gradle.caching=true
org.gradle.configuration-cache=true
org.gradle.parallel=true
kotlin.incremental=true
org.gradle.jvmargs=-Xmx4g -XX:+UseG1GC -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8
```

---

## Classloader Isolation

### Settings Plugin Classloader Pollution (Issue #31034)
Applying custom Project-level plugins alongside settings-level plugins within the same composite included build leaks AGP references into the parent settings classloader.
* **Result:** ClassCastException / `Unable to load class com.android.build.api.dsl.ApplicationExtension`.
* **Fix:** Strictly isolate settings or init plugins into a dedicated included build (`build-logic/settings-convention`) separate from Project-level setups.

### Apply-False Settings Hoisting
Enforce single parent classloader resolution by hoisting heavy plugins at settings-level:
```kotlin
// settings.gradle.kts
plugins {
    id("io.sentry.jvm.gradle") version "6.4.0" apply false
}
```

### Worker API Isolation
Delegate memory-intensive tasks clashing with Gradle runtime libraries to isolated classloaders/processes using Gradle Worker API:
```kotlin
abstract class IsolatedToolTask @Inject constructor(
    private val workerExecutor: WorkerExecutor
) : DefaultTask() {
    @TaskAction
    fun run() {
        val queue = workerExecutor.classLoaderIsolation() // Isolated pool
        queue.submit(IsolatedWorkAction::class.java) { ... }
    }
}
```
