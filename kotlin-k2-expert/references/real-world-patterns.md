# Real-World K2 Patterns (from koin-compiler-plugin)

Read when: implementing production-grade K2 plugins, looking for battle-tested patterns, or solving cross-module discovery, IC tracking, or diagnostic reporting challenges.

Source: [koin-compiler-plugin](https://github.com/InsertKoinIO/koin-compiler-plugin) — native K2 compiler plugin for Koin DI.

## Architecture Overview

```
koin-compiler-plugin/
├── koin-compiler-plugin/           # Compiler plugin (FIR + IR)
│   ├── src/.../plugin/
│   │   ├── KoinPluginComponentRegistrar.kt   # CompilerPluginRegistrar
│   │   ├── KoinPluginRegistrar.kt            # FirExtensionRegistrar
│   │   ├── KoinCommandLineProcessor.kt       # CLI options
│   │   ├── KoinPluginConstants.kt            # Shared constants
│   │   ├── KoinAnnotationFqNames.kt          # Annotation FQN registry
│   │   ├── fir/
│   │   │   ├── KoinModuleFirGenerator.kt     # FIR: generates module() extensions
│   │   │   └── FirKoinLookupRecorder.kt      # IC lookup recording
│   │   └── ir/
│   │       ├── KoinIrExtension.kt            # IR orchestrator (5 phases)
│   │       ├── KoinDSLTransformer.kt         # DSL call rewriting
│   │       ├── KoinAnnotationProcessor.kt    # Annotation → module generation
│   │       ├── KoinStartTransformer.kt       # Entry point transforms
│   │       ├── DslHintGenerator.kt           # Cross-module hints
│   │       ├── CompileSafetyValidator.kt     # Graph validation
│   │       └── ... (24 files total)
│   └── testData/
│       ├── box/                              # Runtime tests by category
│       └── diagnostics/                      # Error tests
├── koin-compiler-gradle-plugin/              # Gradle integration
└── test-apps/                                # Integration tests
```

## Pattern 1: FirExtensionRegistrar — Minimal Surface

```kotlin
// Keep registrar dead simple — just wire extensions
class KoinPluginRegistrar : FirExtensionRegistrar() {
    override fun ExtensionRegistrarContext.configurePlugin() {
        +::KoinModuleFirGenerator    // FirDeclarationGenerationExtension
        +::FirKoinLookupRecorder     // IC lookup recording (FirExtensionSessionComponent)
    }
}
```

**Lesson**: FIR registrar has no access to CompilerConfiguration. All config goes through `CompilerPluginRegistrar.registerExtensions()` → global/thread-local state.

## Pattern 2: Centralized Logger with Daemon Safety

```kotlin
object KoinPluginLogger {
    // Per-thread collector — safe for parallel daemon compilations
    val threadCollector = InheritableThreadLocal<MessageCollector?>()
    @Volatile var fallbackCollector: MessageCollector = MessageCollector.NONE

    val effectiveCollector: MessageCollector
        get() = threadCollector.get() ?: fallbackCollector

    // Plugin options stored as @Volatile — set once in init(), read everywhere
    @Volatile var userLogsEnabled = false; private set
    @Volatile var debugLogsEnabled = false; private set
    @Volatile var compileSafetyEnabled = true; private set

    fun init(collector: MessageCollector, userLogs: Boolean, debug: Boolean, ...) {
        threadCollector.set(collector)
        fallbackCollector = collector
        userLogsEnabled = userLogs
        debugLogsEnabled = debug
        // ...
    }

    // Inline + lambda = zero cost when disabled
    inline fun user(message: () -> String) {
        if (userLogsEnabled) effectiveCollector.report(WARNING, "[Koin] ${message()}")
    }
    inline fun debug(message: () -> String) {
        if (debugLogsEnabled) effectiveCollector.report(WARNING, "[Koin-Debug] ${message()}")
    }
}
```

**Why**: FIR extensions can't receive `CompilerConfiguration`. Global state is the only option — but must be thread-safe for daemon parallelism.

## Pattern 3: Multi-Phase IR Orchestration

```kotlin
class KoinIrExtension(
    private val lookupTracker: LookupTracker?,
    private val expectActualTracker: ExpectActualTracker,
    private val messageCollector: MessageCollector, // captured for THIS compilation
) : IrGenerationExtension {

    override fun generate(module: IrModuleFragment, ctx: IrPluginContext) {
        KoinPluginLogger.bindThreadCollector(messageCollector) // anchor thread
        try {
            // Phase 0: Fill FIR-generated hint bodies
            module.transform(KoinHintTransformer(ctx), null)

            // Phase 1: Collect annotations → generate module extensions
            val processor = KoinAnnotationProcessor(ctx, ...)
            processor.collectAnnotations(module)
            processor.generateModuleExtensions(module)

            // Phase 2: Rewrite DSL calls (single<T>() → single(T::class) { T(get()) })
            val dslTransformer = KoinDSLTransformer(ctx, lookupTracker)
            module.transform(dslTransformer, null)

            // Phase 2.5: Generate cross-module DSL hints
            dslHintGenerator.generateDslDefinitionHints(module, dslTransformer.dslDefinitions)

            // Phase 3: Transform entry points (startKoin<T> → inject modules)
            val startTransformer = KoinStartTransformer(ctx, module, processor, ...)
            module.transform(startTransformer, null)

            // Phase 3.5: Validate call sites against assembled graph
            callSiteValidator.validatePendingCallSites(...)

            // Phase 4: @Monitor instrumentation
            module.transform(KoinMonitorTransformer(ctx), null)
        } finally {
            KoinPluginLogger.unbindThreadCollector()
        }
    }
}
```

**Lessons**:
- Capture `MessageCollector` at construction — don't read from singleton during IR
- `bindThreadCollector` at start of `generate()` — IR may run on different thread than registration
- Phase ordering: collection → generation → transformation → validation → instrumentation
- Each phase produces state consumed by later phases (dslDefinitions, processor state, etc.)

## Pattern 4: Cross-Module Discovery via Hint Functions

Compiler plugins can't scan pre-compiled JARs. Solution: generate synthetic functions whose signatures encode metadata.

```
FIR phase: generate function signature
  fun koin_hint_single_com_example_UserRepo(): UserRepository
  fun koin_hint_factory_com_example_GetUser(): GetUserUseCase

IR phase: fill with empty body (return Unit / throw)

Consumer module: discover via pluginContext.referenceFunctions(CallableId(...))
  → parse function name for prefix, type for provided binding
```

**Pattern details**:
- Function name: `<prefix>_<flat_fqn>` — encodes definition type + class
- Return type: the provided type (what the definition makes available)
- Parameters: constructor dependencies (what it needs)
- Visibility: internal + `@Deprecated(level = HIDDEN)` — invisible to users

## Pattern 5: Configuration via Gradle Extension → CLI → CompilerConfiguration

```
Gradle Extension (user-facing DSL)
  ↓ SubpluginOption("key", "value")
CommandLineProcessor
  ↓ configuration.put(ConfigKey, value)
CompilerPluginRegistrar
  ↓ configuration.get(ConfigKey, default)
Global state (KoinPluginLogger.init())
  ↓ @Volatile fields
FIR + IR extensions read global state
```

```kotlin
// Gradle extension
open class KoinGradleExtension {
    var userLogs: Boolean = false
    var debugLogs: Boolean = false
    var compileSafety: Boolean = true
    var strictSafety: Boolean? = null  // null = auto-detect
}

// CLI processor
object KoinConfigurationKeys {
    val USER_LOGS = CompilerConfigurationKey<Boolean>("user logs")
    val DEBUG_LOGS = CompilerConfigurationKey<Boolean>("debug logs")
    val COMPILE_SAFETY = CompilerConfigurationKey<Boolean>("compile safety")
}
```

## Pattern 6: Diagnostic Reporting with Codes

```kotlin
sealed class KoinDiagnostic(val code: String, val message: String, val severity: Severity) {
    enum class Severity { ERROR, WARNING }

    class MissingDefinition(type: String, consumer: String) : KoinDiagnostic(
        "KOIN-D001",
        "No definition found for '$type' required by '$consumer'",
        Severity.ERROR
    )
    class UnusedDefinition(type: String) : KoinDiagnostic(
        "KOIN-W001",
        "Definition '$type' is never injected",
        Severity.WARNING
    )
}

// Report with source location
fun report(diagnostic: KoinDiagnostic, filePath: String?, line: Int, col: Int) {
    val location = filePath?.let { CompilerMessageLocation.create(it, line, col, null) }
    val severity = when (diagnostic.severity) {
        ERROR -> CompilerMessageSeverity.ERROR
        WARNING -> CompilerMessageSeverity.WARNING
    }
    effectiveCollector.report(severity, "[Koin][${diagnostic.code}] ${diagnostic.message}", location)
}
```

## Pattern 7: Test Organization by Feature

```
testData/box/
├── dsl/               # DSL function transformations
│   ├── singleBasic.kt
│   ├── factoryWithDeps.kt
│   └── viewModelParams.kt
├── annotations/       # Annotation processing
│   ├── singletonClass.kt
│   └── factoryFunction.kt
├── qualifiers/        # @Named, @Qualifier
├── params/            # @InjectedParam, @Property, Lazy<T>
├── modules/           # @Module, @ComponentScan
├── startkoin/         # startKoin, koinApplication
├── scopes/            # @Scoped, @Scope
├── toplevel/          # Top-level function definitions
└── bindings/          # Interface auto-binding
```

Each test: self-contained `.kt` file with `fun box(): String`. Golden files alongside (`*.fir.txt`, `*.fir.ir.txt`).

**Update golden files**: `./gradlew test -Pupdate.testdata=true`

## Key Takeaways

1. **FIR = signatures, IR = bodies** — never violate this boundary
2. **Daemon parallelism is real** — InheritableThreadLocal + captured collectors
3. **IC is coarser than you think** — lambda body changes invisible, force aggregator recompilation
4. **Cross-module = hint functions** — encode metadata in function signatures
5. **Phase ordering matters** — collect → generate → transform → validate
6. **Diagnostics need locations** — clickable errors in IDE are essential for UX
7. **Config flows Gradle → CLI → Configuration → global state** — accept the pattern
8. **Test by category** — organize testData/box/ by feature area with golden snapshots
