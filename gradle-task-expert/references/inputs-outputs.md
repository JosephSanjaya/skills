# Task Inputs, Outputs, and Managed Properties (Gradle 9.5.1+)

For Gradle to perform up-to-date checks (incremental builds), cache task outputs, and infer task execution order, tasks must precisely model their inputs and outputs.

---

## 1. Managed Properties

Modern Gradle tasks use **Managed Properties** instead of raw fields. Managed properties are abstract JVM properties instantiated automatically by Gradle. They support lazy evaluation, tracking dependency sources, and clean configuration.

### Supported Managed Types

- `Property<T>`: A container for single values (e.g., `Property<String>`, `Property<Boolean>`).
- `ListProperty<T>` / `SetProperty<T>`: Lazy lists/sets of values.
- `MapProperty<K, V>`: Lazy map collections.
- `RegularFileProperty`: A lazy pointer to a single file.
- `DirectoryProperty`: A lazy pointer to a directory.

---

## 2. Kotlin Getter Annotation Requirement

> [!IMPORTANT]
> In Kotlin, properties declared in class headers generate private fields and public getters/setters. Gradle's task validation engine scans public getters. 
> Therefore, in Kotlin DSL custom tasks, **you must use the `@get:` prefix for task annotations**. Placing annotations directly (e.g., `@Input`) will place them on the private field, and Gradle will ignore them, resulting in task verification warnings or failures.

### Anti-Pattern: Ignored Field Annotations
```kotlin
// AVOID: Gradle ignores these because the annotation is attached to the private field
abstract class IncorrectTask : DefaultTask() {
    @Input
    abstract val message: Property<String>

    @OutputFile
    abstract val output: RegularFileProperty
}
```

### Correct Pattern: Getter-Targeted Annotations
```kotlin
// PREFER: Gradle maps these correctly
abstract class CorrectTask : DefaultTask() {
    @get:Input
    abstract val message: Property<String>

    @get:OutputFile
    abstract val output: RegularFileProperty
}
```

---

## 3. Input and Output Annotations Reference

Every public property in a custom task class **must** have a task annotation. The most common annotations include:

| Annotation | Type | Description |
|---|---|---|
| `@get:Input` | `Property<T>`, primitives, Serializable | A simple scalar input value affecting task behavior. |
| `@get:InputFile` | `RegularFileProperty` | An input file whose path and content affect the task. |
| `@get:InputDirectory` | `DirectoryProperty` | An input directory. |
| `@get:InputFiles` | `ListProperty<RegularFile>`, `FileCollection` | Multiple files/folders. |
| `@get:OutputFile` | `RegularFileProperty` | The single output file produced by the task. |
| `@get:OutputDirectory` | `DirectoryProperty` | The output directory produced by the task. |
| `@get:Internal` | Any type | Properties that do not participate in caching or up-to-date checks (e.g., helpers, loaders). |

---

## 4. Path Sensitivity & Cache Normalization

File and directory inputs **must** define a path sensitivity. Without path sensitivity, a task's cache key depends on the absolute path of its inputs, preventing cache sharing across different machines or checkouts.

```kotlin
@get:PathSensitive(PathSensitivity.NONE)
@get:InputFile
abstract val apk: RegularFileProperty
```

### Path Sensitivity Options

- **`PathSensitivity.NONE`**: Only the file content matters. Relocation-friendly (ideal for compile classpaths, resource bundles, or independent artifacts).
- **`PathSensitivity.RELATIVE`**: The file content and its path relative to the input root matter (ideal for source files, assets, or compile targets).
- **`PathSensitivity.ABSOLUTE`**: The absolute path matters. **Avoid** unless absolute paths are hardcoded in compilation/execution output.

---

## 5. Incremental Tasks with `InputChanges`

If a task has many input files and can process only the files that changed since the last execution, it should use an **Incremental Task Action**.

To implement an incremental task:
1. Mark the incremental input files property with `@Incremental` or `@SkipWhenEmpty`.
2. Add a single `InputChanges` parameter to the `@TaskAction` function.

> [!IMPORTANT]
> **Incremental Task Package Pitfall**:
> - `InputChanges` and `ChangeType` reside in the **`org.gradle.work`** package.
> - `FileType` resides in the **`org.gradle.api.file`** package.
> 
> A common mistake is attempting to import `org.gradle.work.FileType`, which does not exist and will fail to compile.

```kotlin
import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.file.FileType
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.tasks.*
import org.gradle.work.Incremental
import org.gradle.work.InputChanges

abstract class IncrementalProcessTask : DefaultTask() {

    @get:Incremental
    @get:PathSensitive(PathSensitivity.RELATIVE)
    @get:InputDirectory
    abstract val inputDir: DirectoryProperty

    @get:OutputFile
    abstract val report: RegularFileProperty

    @TaskAction
    fun process(inputChanges: InputChanges) {
        val changes = inputChanges.getFileChanges(inputDir)
        changes.forEach { change ->
            if (change.fileType == FileType.DIRECTORY) return@forEach
            
            when (change.changeType) {
                ChangeType.ADDED, ChangeType.MODIFIED -> {
                    // Process new or changed file
                }
                ChangeType.REMOVED -> {
                    // Clean up removed file
                }
            }
        }
    }
}
```
