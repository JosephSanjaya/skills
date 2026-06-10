# K2 Optimization Patterns

Read when: optimizing compiler plugin performance, implementing caching, handling incremental compilation, daemon safety, or lazy classpath scanning.

## 1. Provider-Based On-Demand Generation

K1's `SyntheticResolveExtension` eagerly generated all members. K2's `FirDeclarationGenerationExtension` is strictly lazy — compiler queries by name.

**Rules**:
- `getCallableNamesForClass()` → return Set<Name> of what you CAN generate. Fast, no allocations.
- `getTopLevelCallableIds()` → same for top-level functions/properties.
- `generateFunctions()/generateProperties()` → only called when compiler needs that specific name.
- Never re-parse constructors or search classes inside generate functions.
- Attach metadata to `GeneratedDeclarationKey` subclass for O(1) retrieval later.

```kotlin
object MyKey : GeneratedDeclarationKey() {
    // Attach generation metadata here if needed
}

override fun getCallableNamesForClass(classSymbol: FirClassSymbol<*>, context: MemberGenerationContext): Set<Name> {
    // FAST: just check annotation presence, return hardcoded name set
    return if (classSymbol.hasAnnotation(TARGET, session)) GENERATED_NAMES else emptySet()
}

override fun generateFunctions(callableId: CallableId, context: MemberGenerationContext?): List<FirNamedFunctionSymbol> {
    // Extract metadata from context.owner's origin — O(1), no re-parsing
    val ownerKey = context?.owner?.origin as? FirDeclarationOrigin.Plugin
    // Build and return function signature (no body)
    return listOf(buildSignature(callableId, MyKey))
}

private companion object {
    val TARGET = ClassId.topLevel(FqName("com.example.AutoGenerate"))
    val GENERATED_NAMES = setOf(Name.identifier("create"), Name.identifier("factory"))
}
```

## 2. Lazy Classpath Resolution

**Anti-pattern**: eager classpath scanning in `CompilerPluginRegistrar` → kills IC + IDE.

**Pattern**: offload to `FirExtensionSessionComponent` with lazy initialization.

```kotlin
class ClasspathIndexer(session: FirSession) : FirExtensionSessionComponent(session) {

    // Lazy — only scans when first queried
    private val annotatedTypes: Map<ClassId, AnnotationData> by lazy {
        val roots = session.moduleData.platform // or from saved config
        scanClasspath(roots)
    }

    fun findAnnotated(annotation: ClassId): List<ClassId> {
        return annotatedTypes.filterValues { it.hasAnnotation(annotation) }.keys.toList()
    }

    private fun scanClasspath(roots: Any): Map<ClassId, AnnotationData> {
        // ClassGraph or manual JAR scan
        // CRITICAL: FirSession persists across IC steps in daemon
        // → scan once, reuse across incremental builds
        return emptyMap()
    }
}

// Register in FirExtensionRegistrar:
class MyFirRegistrar : FirExtensionRegistrar() {
    override fun ExtensionRegistrarContext.configurePlugin() {
        +::ClasspathIndexer  // FirExtensionSessionComponent
        +::MyGenerator
    }
}

// Access in generator:
class MyGenerator(session: FirSession) : FirDeclarationGenerationExtension(session) {
    private val indexer = session.extensionSessionComponent<ClasspathIndexer>()
}
```

## 3. Daemon-Parallel Safety

K2 daemon can run multiple compilations concurrently. Volatile singletons race.

**Pattern**: `InheritableThreadLocal` for per-compilation state.

```kotlin
object PluginLogger {
    // Per-thread collector — inherits to child threads (IR fan-out)
    private val threadCollector = InheritableThreadLocal<MessageCollector?>()
    @Volatile private var fallback: MessageCollector = MessageCollector.NONE

    val effective: MessageCollector
        get() = threadCollector.get() ?: fallback

    fun init(collector: MessageCollector) {
        threadCollector.set(collector)
        fallback = collector
    }

    // Re-bind on IR thread (may differ from registration thread)
    fun bindThread(collector: MessageCollector) { threadCollector.set(collector) }
    fun unbindThread() { threadCollector.remove() }

    inline fun log(msg: () -> String) {
        effective.report(CompilerMessageSeverity.WARNING, "[Plugin] ${msg()}")
    }
}

// In IrGenerationExtension:
class MyIrExtension(private val collector: MessageCollector) : IrGenerationExtension {
    override fun generate(module: IrModuleFragment, ctx: IrPluginContext) {
        PluginLogger.bindThread(collector) // anchor to THIS compilation
        try {
            // ... IR processing
        } finally {
            PluginLogger.unbindThread()
        }
    }
}
```

**Why `InheritableThreadLocal`**: `init()` runs on registration thread. IR generation may run on different daemon pool thread. Without re-binding, collector slot is empty → falls to fallback → parallel compilation may have overwritten it.

## 4. Incremental Compilation Workarounds

### Problem: Lambda body changes invisible to IC

Kotlin IC tracks per-declaration ABI changes. Lambda bodies aren't ABI. Adding/removing `single<X>()` inside `module { }` → no IC signal → aggregator skips recompilation → stale graph.

### Problem: Package-level scanning misses new files

`@ComponentScan("com.pkg")` works by package — no source-level edge to specific files. New `@Singleton class X` in scanned package → nothing references it → IC can't invalidate.

### Solution: Force aggregator recompilation

```kotlin
// In Gradle plugin, for aggregator modules only:
class MyGradlePlugin : KotlinCompilerPluginSupportPlugin {
    override fun apply(target: Project) {
        target.afterEvaluate {
            if (isAggregatorModule(target)) {
                target.tasks.named("compileKotlin") {
                    outputs.upToDateWhen { false }
                }
            }
        }
    }

    private fun isAggregatorModule(project: Project): Boolean {
        // Scan sources for startKoin/koinApplication/@KoinApplication
        return project.fileTree("src").files.any { file ->
            file.readText().contains("startKoin") || file.readText().contains("@KoinApplication")
        }
    }
}
```

**Cost**: bounded. Only aggregator module re-runs `compileKotlin`. Leaf modules stay fully incremental.

### ExpectActualTracker for file-pair links

Record file dependencies so IC knows to re-run when paired files change:

```kotlin
expectActualTracker.report(
    /* expectedFile */ aggregatorSourceFile,
    /* actualFile */ generatedHintFile
)
```

Only fires when both files participate in build — doesn't cover newly-introduced files.

## 5. Multi-Phase IR Orchestration

Real-world plugins need ordered phases. Pattern from koin-compiler-plugin:

```kotlin
class MyIrExtension : IrGenerationExtension {
    override fun generate(module: IrModuleFragment, ctx: IrPluginContext) {
        // Phase 0: Fill FIR-generated stub bodies
        module.transform(HintBodyTransformer(ctx), null)

        // Phase 1: Collect + generate (annotation processing)
        val processor = AnnotationProcessor(ctx)
        processor.collect(module)
        processor.generate(module)

        // Phase 2: Transform DSL calls (rewrite function bodies)
        val dslTransformer = DslTransformer(ctx)
        module.transform(dslTransformer, null)

        // Phase 3: Transform entry points (inject module lists)
        val startTransformer = StartTransformer(ctx, module, processor)
        module.transform(startTransformer, null)

        // Phase 4: Validation (check graph completeness)
        if (safetyEnabled) {
            validator.validateGraph(module, processor, dslTransformer)
        }
    }
}
```

**Key**: each phase writes state consumed by later phases. Never merge phases that depend on each other.

## 6. Performance Checklist

| Area | Do | Don't |
|---|---|---|
| FIR generation | Return hardcoded name sets | Scan classpath in getCallableNames |
| Classpath | Lazy scan in SessionComponent | Eager scan in registerExtensions |
| Caching | Cache in FirSession (persists in daemon) | Cache in companion objects (lost on restart) |
| Logging | Inline lambdas: `log { "msg" }` | String concat: `log("msg " + x)` |
| IC | Record lookup/expect-actual tracking | Ignore IC trackers |
| Threading | InheritableThreadLocal for state | Volatile singletons for mutable state |
| IR passes | Separate stubs from bodies | Single-pass with forward references |
| Gradle | Config cache compatible (ObjectFactory) | Direct Project references in tasks |
| Memory | `org.gradle.jvmargs=-Xmx3g` | Default heap for multi-module |
| Exports | `transitiveExport = false` | Leaking transitive deps |
