# Testing and Debugging Gradle Tasks (Gradle 9.5.1+)

To verify that tasks behave correctly, perform up-to-date checks as expected, and do not violate configuration cache rules, Gradle provides a structured testing pyramid and built-in diagnostic tools.

---

## 1. Unit Testing with `ProjectBuilder`

Unit tests verify task registration, configuration, and default inputs/outputs without executing the actual task actions. They are fast because they run entirely in-memory.

```kotlin
import org.gradle.testfixtures.ProjectBuilder
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import java.io.File

class CustomTaskUnitTest {

    @Test
    fun `task is registered and configured correctly`() {
        val project = ProjectBuilder.builder().build()
        
        // Register the task
        val taskProvider = project.tasks.register("myCustomTask", GreetingTask::class.java) {
            greeting.set("Hello Test")
        }

        val task = taskProvider.get()
        
        // Assertions
        assertEquals("Hello Test", task.greeting.get())
        assertTrue(task.enabled)
    }
}
```

---

## 2. Functional Testing with Gradle TestKit (`GradleRunner`)

Functional tests run real Gradle builds against a temporary filesystem workspace. They are the only way to verify:
- Actual task execution outcomes (`SUCCESS`, `FAILED`, `UP-TO-DATE`, `FROM-CACHE`).
- Incremental execution and input/output cache hits.
- Configuration Cache compatibility.

```kotlin
import org.gradle.testkit.runner.GradleRunner
import org.gradle.testkit.runner.TaskOutcome
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.io.File

class CustomTaskFunctionalTest {

    @TempDir
    lateinit var testProjectDir: File
    private lateinit var buildFile: File

    @BeforeEach
    fun setup() {
        buildFile = File(testProjectDir, "build.gradle.kts")
    }

    @Test
    fun `task executes successfully and is up-to-date on second run`() {
        // Write build script
        buildFile.writeText("""
            plugins {
                base
            }
            
            abstract class SimpleTask : DefaultTask() {
                @get:OutputFile
                abstract val output: RegularFileProperty
                
                @TaskAction
                fun run() {
                    output.get().asFile.writeText("hello")
                }
            }
            
            tasks.register<SimpleTask>("simple") {
                output.set(layout.buildDirectory.file("out.txt"))
            }
        """.trimIndent())

        // Run the first build
        val result = GradleRunner.create()
            .withProjectDir(testProjectDir)
            .withArguments("simple", "--configuration-cache")
            .withPluginClasspath()
            .build()

        assertEquals(TaskOutcome.SUCCESS, result.task(":simple")?.outcome)

        // Run the second build (should be UP-TO-DATE and load from Configuration Cache)
        val secondResult = GradleRunner.create()
            .withProjectDir(testProjectDir)
            .withArguments("simple", "--configuration-cache")
            .withPluginClasspath()
            .build()

        assertEquals(TaskOutcome.UP_TO_DATE, secondResult.task(":simple")?.outcome)
        assertTrue(secondResult.output.contains("Reusing configuration cache"))
    }
}
```

---

## 3. CLI Debugging & Diagnostics

Gradle has powerful built-in CLI flags to diagnose task graph registration, task dependencies, and cache states:

| Command / Flag | Purpose | Description |
|---|---|---|
| `./gradlew tasks --provenance` | Task Registration Search | Shows which plugin or build script registered each task. |
| `./gradlew help --task <taskName>`| Task Definition Audit | Displays details on task type, path, inputs, outputs, and description. |
| `./gradlew <task> --scan` | Build Scan Diagnostic | Generates a web-based performance analysis report. |
| `--info` | Informational Logs | Outputs reasons why tasks are out-of-date and did not hit cache. |
| `--debug` | Trace Logs | Shows deep internal stack traces and engine decisions. |

### Inspecting Task Input/Output Details via `help --task`
Executing `help --task <taskName>` exposes exact task parameters:
```bash
$ ./gradlew help --task compileJava

Detailed task information for compileJava

Path
     :compileJava

Type
     JavaCompile (org.gradle.api.tasks.compile.JavaCompile)

Description
     Compiles Java source files.

Inputs
     options.compilerArgs: []
     options.encoding: UTF-8
     source: [/path/to/src/main/java/Main.java]
     toolChain: JDK 17 (17)

Outputs
     destinationDirectory: /path/to/build/classes/java/main
```
