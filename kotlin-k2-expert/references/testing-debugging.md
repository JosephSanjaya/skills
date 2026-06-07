# K2 Plugin Testing & Debugging

Read when: writing tests for compiler plugins, debugging IR generation, using golden file snapshots, or tracing compilation issues.

## Test Infrastructure Setup

### Dependencies (compiler-plugin/build.gradle.kts)

```kotlin
dependencies {
    compileOnly("org.jetbrains.kotlin:kotlin-compiler-embeddable")

    testImplementation("org.jetbrains.kotlin:kotlin-compiler-internal-test-framework")
    testImplementation(kotlin("test"))
    testRuntimeOnly("org.jetbrains.kotlin:kotlin-test")
    testRuntimeOnly("org.jetbrains.kotlin:kotlin-scripting-compiler")
    testRuntimeOnly("org.jetbrains.kotlin:kotlin-annotations-jvm")
    testImplementation(project(":annotations"))
}

tasks.test {
    useJUnitPlatform()
    systemProperty("testData.dir", file("testData").absolutePath)
}
```

### Directory Structure

```
testData/
├── box/                     # Runtime tests — execute generated code
│   ├── simpleGeneration.kt
│   ├── factoryPattern.kt
│   └── multiModule/
│       ├── moduleA.kt
│       └── moduleB.kt
└── diagnostics/             # Compile-time tests — verify errors/warnings
    ├── missingAnnotation.kt
    └── invalidConfiguration.kt
```

## Box Tests (Runtime Verification)

Convention: `fun box(): String` returns `"OK"` on success, anything else = failure.

```kotlin
// testData/box/simpleGeneration.kt
package test

import com.example.annotations.AutoGenerate

@AutoGenerate
class Target

fun box(): String {
    val target = Target()
    // Test that compiler plugin injected "generatedMethod"
    val result = target.generatedMethod()
    return if (result == "Expected Value") "OK" else "Fail: $result"
}
```

### Multi-file box test

```kotlin
// testData/box/multiFile/moduleA.kt
// FILE: moduleA.kt
package test

@AutoGenerate
class ServiceA {
    fun getData() = "data"
}

// FILE: moduleB.kt
package test

fun box(): String {
    val a = ServiceA()
    return if (a.generatedMethod() == "data_processed") "OK" else "Fail"
}
```

### Test runner

```kotlin
class BoxTestGenerated : AbstractBoxTest() {
    fun testSimpleGeneration() { runTest("testData/box/simpleGeneration.kt") }
    fun testFactoryPattern() { runTest("testData/box/factoryPattern.kt") }
}

abstract class AbstractBoxTest : AbstractIrTextTest() {
    override fun createCompilerConfiguration(): CompilerConfiguration {
        return super.createCompilerConfiguration().apply {
            // Register your plugin
            add(CompilerPluginRegistrar.COMPILER_PLUGIN_REGISTRARS, MyPluginRegistrar())
        }
    }
}
```

## Diagnostics Tests

Verify custom checkers report errors/warnings at correct positions.

```kotlin
// testData/diagnostics/missingAnnotation.kt
package test

// Expect error at line with missing required annotation
class <!MISSING_AUTO_GENERATE!>InvalidTarget<!> {
    fun doStuff() {}
}
```

Markers: `<!DIAGNOSTIC_NAME!>text<!>` wraps code where diagnostic should fire.

## Golden Files (Snapshot Testing)

Framework auto-generates:
- `*.fir.txt` — FIR tree representation (post-frontend)
- `*.fir.ir.txt` — IR tree representation (post-backend)

Workflow:
1. First run: golden files created automatically
2. Subsequent runs: compared against existing
3. Update goldens: run with `-Pupdate.testdata=true`

```bash
# Run tests
./gradlew :compiler-plugin:test

# Update golden files after intentional changes
./gradlew :compiler-plugin:test -Pupdate.testdata=true

# Run specific test
./gradlew :compiler-plugin:test --tests "*SimpleGeneration*"
```

## Compiler Debugging Flags

### -Xverify-ir

Validates IR tree structural correctness BEFORE bytecode generation. Catches:
- Type mismatches between declaration and usage
- Unresolved symbol references
- Scope leaks (declarations visible outside intended scope)
- Missing or duplicate declarations

```kotlin
// In build.gradle.kts of test project
kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xverify-ir")
    }
}
```

**Always enable during development and testing.** Catches issues that would otherwise silently produce wrong bytecode.

### -Xphases-to-dump-before / -Xphases-to-dump-after

Dumps IR tree at specific compilation phases. Useful for comparing expected vs actual IR.

```kotlin
freeCompilerArgs.addAll(
    "-Xphases-to-dump-before=ExternalPackageParentPatcherLowering",
    "-Xdump-directory=${layout.buildDirectory.dir("ir-dumps").get().asFile.absolutePath}"
)
```

Common phases to dump:
- `ExternalPackageParentPatcherLowering` — early, shows raw plugin output
- `InnerClassesLowering` — after inner class restructuring
- `JvmDefaultArgumentStubGenerator` — after default arg processing

### Debug workflow

1. Write target output manually (what you EXPECT the plugin to generate)
2. Dump IR with `-Xphases-to-dump-before`
3. Compare manual IR against plugin's synthetic IR
4. Identify discrepancies in generation pipeline

## Diagnostic Reporting with Source Locations

```kotlin
import org.jetbrains.kotlin.cli.common.messages.*

// Simple error
messageCollector.report(
    CompilerMessageSeverity.ERROR,
    "[MyPlugin] Missing required annotation on class ${className}"
)

// Error with source location (clickable in IDE)
messageCollector.report(
    CompilerMessageSeverity.ERROR,
    "[MyPlugin] Invalid configuration",
    CompilerMessageLocation.create(filePath, lineNumber, columnNumber, null)
)

// Typed diagnostics with severity tracking
sealed class MyDiagnostic(val code: String, val message: String, val severity: Severity) {
    enum class Severity { ERROR, WARNING }

    class MissingDep(type: String) : MyDiagnostic(
        "E001", "Missing dependency: $type", Severity.ERROR
    )
    class DeprecatedUsage(api: String) : MyDiagnostic(
        "W001", "Deprecated API: $api", Severity.WARNING
    )
}
```

## Common Debugging Issues

### "Unresolved reference" to generated declaration
- **Cause**: declaration only exists in IR, not registered in FIR
- **Fix**: add FirDeclarationGenerationExtension that returns the declaration signature

### Symbol table corruption / crash in IR
- **Cause**: single-pass generation with forward references
- **Fix**: implement two-pass (stubs-before-bodies) pattern

### IDE shows red underlines but code compiles
- **Cause**: third-party plugin not enabled in K2 Mode
- **Fix**: Registry → uncheck `kotlin.k2.only.bundled.compiler.plugins.enabled`

### Incremental build misses changes
- **Cause**: lambda body changes don't trigger IC
- **Fix**: `strictSafety = true` or `outputs.upToDateWhen { false }` on aggregator

### Generated code works in clean build but fails incrementally
- **Cause**: stale cached symbols from previous compilation
- **Fix**: verify FirSession caching invalidates correctly; check LookupTracker recording

### Wrong thread's MessageCollector in parallel daemon
- **Cause**: volatile singleton overwritten by concurrent compilation
- **Fix**: InheritableThreadLocal + bind/unbind in IrGenerationExtension.generate()
