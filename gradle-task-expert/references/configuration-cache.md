# Task Compatibility with Configuration Cache (Gradle 9.5.1+)

The **Configuration Cache** speeds up builds by caching the output of the configuration phase (the task graph) and reusing it on subsequent runs. To ensure tasks are configuration cache compliant, they must be fully serializable and must not access shared build state or early resolved values during execution.

---

## 1. No Project Leaks (The Golden Rule)

A task action (`@TaskAction`, `doFirst`, `doLast`) **must never** reference the `Project` instance (e.g., `project.files()`, `project.logger`, `project.rootDir`, `project.properties`). Any reference to `Project` inside these execution closures will cause configuration cache failures.

### Anti-Pattern: Accessing `project` in Task Action
```kotlin
tasks.register("leakyTask") {
    // Configuration closure
    val outputDir = project.layout.buildDirectory.dir("outputs")
    
    doLast {
        // AVOID: Accessing `project` here leaks the Project instance into the execution block!
        val file = project.file("${outputDir.get().asFile}/out.txt")
        file.writeText("data")
    }
}
```

### Correct Pattern: Capture values in Configuration, use them in Execution
```kotlin
tasks.register("cleanTask") {
    // Configuration closure: resolve providers/properties early
    val outputDir = layout.buildDirectory.dir("outputs")
    val fileProvider = outputDir.map { it.file("out.txt") }
    
    doLast {
        // PREFER: Accessing `fileProvider` (which is a serializable Provider), NOT `project`
        val file = fileProvider.get().asFile
        file.writeText("data")
    }
}
```

---

## 2. Injected Services for Actions

If you need capabilities typically provided by the `Project` instance (such as process execution, file operations, or logging), you must inject them using Gradle's **Injected Services** mechanism.

In custom task classes, use `@get:Inject` on abstract properties of the service type. Gradle will automatically inject the service instance at runtime:

| Project API (Avoid in Action) | Service Replacement (Inject) | Purpose |
|---|---|---|
| `project.exec { ... }` | `ExecOperations` | Executing system commands. |
| `project.copy { ... }` | `FileSystemOperations` | Copying or deleting files dynamically. |
| `project.logger` | `ObjectFactory` (or default task `logger`) | Logging task progress. |

### Configuration Cache Compliant Command Execution
```kotlin
import org.gradle.api.DefaultTask
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import org.gradle.process.ExecOperations
import javax.inject.Inject

abstract class RunScriptTask : DefaultTask() {

    @get:InputFile
    abstract val script: RegularFileProperty

    @get:OutputFile
    abstract val result: RegularFileProperty

    // Injected service for running processes
    @get:Inject
    abstract val execOperations: ExecOperations

    @TaskAction
    fun run() {
        execOperations.exec {
            commandLine("bash", script.get().asFile.absolutePath)
            standardOutput = result.get().asFile.outputStream()
        }
    }
}
```

---

## 3. Lazily Reading Environment, System Properties, and Files

Reading environment variables, system properties, or files eagerly during the configuration phase forces Gradle to treat them as configuration cache inputs. If they change, the entire configuration cache is invalidated.

Always read these values lazily using Gradle's `ValueSource` or the `providers` API:

```kotlin
// AVOID: Eager environment variable read during configuration
val apiKey = System.getenv("API_KEY")

// PREFER: Lazy environment variable provider (only read when task executes)
val apiKeyProvider = providers.environmentVariable("API_KEY")
```

### Lazy Value Provider Matrix

| Eager API (Avoid) | Lazy API (Prefer) | Why |
|---|---|---|
| `System.getenv("VAR")` | `providers.environmentVariable("VAR")` | Defers reading until execution. |
| `System.getProperty("prop")` | `providers.systemProperty("prop")` | Cache-safe system property lookup. |
| `project.findProperty("key")` | `providers.gradleProperty("key")` | Cache-safe Gradle property lookup. |
| `File("config.txt").readText()`| `providers.fileContents(layout.projectDirectory.file("config.txt")).asText` | Cache-safe file contents reading. |

---

## 4. Secrets Caching Warning

> [!WARNING]
> Because Gradle serializes task inputs and the execution graph to `.gradle/configuration-cache/`, any secrets passed to tasks via properties or env vars will be written to disk in plain text inside the configuration cache folder.
> - **Exempt secrets from caching**: If your task requires a dynamic security credential, do not mark it as a task `@Input` directly. Instead, retrieve it inside the task action using an injected credential manager, or mark it as an `@Internal` property and load it on-demand.
