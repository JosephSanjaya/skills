---
name: kotlin-k2-expert
description: >
  Expert knowledge for Kotlin K2 compiler plugin development, architecture, optimization,
  and Kotlin 2.4.0 compatibility. Use when: building K2 compiler plugins (FIR + IR),
  debugging FIR/IR generation issues, implementing FirDeclarationGenerationExtension or
  IrGenerationExtension, migrating K1 plugins to K2, understanding FIR pipeline lifecycle
  stages, implementing two-pass IR generation, lazy classpath resolution, provider-based
  on-demand generation, CompilerPluginRegistrar setup, FirExtensionRegistrar configuration,
  Gradle plugin wiring for compiler plugins, testing with Kotlin compiler test infrastructure,
  debugging with -Xverify-ir/-Xphases-to-dump-before, handling Kotlin 2.4.0 breaking changes
  (context parameters, explicit backing fields, annotation target defaults, Jakarta nullability),
  K2 IDE integration, incremental compilation with compiler plugins, cross-module symbol
  discovery via hint functions, daemon-parallel safety patterns, or any K2 FIR/IR question.
---

# Kotlin K2 Compiler Plugin Expert

<instructions>
This skill provides workflow guidance, architectural blueprints, and troubleshooting rules for K2 compiler plugin development. When assisting with Kotlin K2 plugins, enforce the following structured constraints:
1. **Delineate Frontend & Backend**: Ensure all frontend declarations (signatures) are registered via `FirDeclarationGenerationExtension` and all backend implementations (bodies) are transformed via `IrGenerationExtension`.
2. **Use Lazy Provider APIs**: Never scan classpaths eagerly or perform expensive lookups during compilation. Utilize `FirExtensionSessionComponent` for persistent session caching.
3. **Ensure Thread Safety**: All mutable state inside parallel daemon compilations must be wrapped in `InheritableThreadLocal` variables and tied to the active IR phase lifecycle.
</instructions>

## K2 vs K1 Architecture

K1's bottleneck is the monolithic, PSI-keyed `BindingContext`. K2 introduces **FIR (Frontend Intermediate Representation)**, a unified semantic AST that resolves types lazily and restricts random jumps to supertype and implicit type resolution.

| Metric | K1 | K2 | Gain |
|---|---|---|---|
| Clean build | 57.7s | 29.7s | ~94% |
| Incremental init | 0.126s | 0.022s | ~488% |
| Incremental analysis | 0.581s | 0.122s | ~376% |

## FIR-to-IR Compilation Pipeline

Plugin code must follow the compilation phases. Frontend extensions register declarations, while backend extensions lower the AST and implement bodies.

| Phase | Stage | Plugin Extension Point |
|---|---|---|
| 1 | Parsing → PSI | *None* |
| 2 | Raw FIR build | *None* |
| 3 | Supertype resolution | `FirSupertypeGenerationExtension` |
| 4 | Status (visibility/modality) | `FirStatusTransformerExtension` |
| 5 | Callable generation | `FirDeclarationGenerationExtension` |
| 6 | Annotation arguments | `FirTypeAttributeExtension` |
| 7 | Diagnostics/checkers | `FirAdditionalCheckersExtension` |
| 8 | Fir2Ir translation | `FirBasedSignatureComposer` |
| 9 | IR lowering | `IrGenerationExtension` |

> [!NOTE]
> The symbol bridge mapping is established using `FirDeclarationOrigin.Plugin` and a custom `FirPluginKey`. This maps directly to `IrDeclarationOrigin.GeneratedByPlugin(key)` during the Fir2Ir phase.

## Three-Module Project Architecture

Build K2 compiler plugins using a three-module setup:
1. `gradle-plugin`: Contains the `KotlinCompilerPluginSupportPlugin` implementation.
2. `compiler-plugin`: Holds the actual compiler extensions (`CompilerPluginRegistrar`, FIR, IR).
3. `annotations`: A lightweight, compile-only module containing runtime annotations.

```kotlin
// CompilerPluginRegistrar - Plugin entry point
class MyRegistrar : CompilerPluginRegistrar() {
    override val supportsK2 = true
    override fun ExtensionStorage.registerExtensions(config: CompilerConfiguration) {
        FirExtensionRegistrarAdapter.registerExtension(MyFirRegistrar())
        IrGenerationExtension.registerExtension(MyIrExtension())
    }
}
```

Detailed setup, service registrations, and build scripts: [plugin-blueprint.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/plugin-blueprint.md)

## FIR Generation (Lazy & Provider-Based)

In K2, eager synthetic resolution is replaced by a lazy query-based API. The compiler queries the extension for names, and signatures are generated on-demand.

*   Return candidate name sets in `getCallableNamesForClass()` to signal what your plugin can generate.
*   Avoid executing expensive operations or resolution logic inside signature generators.
*   Cache state in `FirExtensionSessionComponent` to avoid duplicate computation.

```kotlin
class MyGenerator(session: FirSession) : FirDeclarationGenerationExtension(session) {
    object MyKey : GeneratedDeclarationKey()

    override fun getCallableNamesForClass(classSymbol: FirClassSymbol<*>): Set<Name> {
        if (!classSymbol.hasAnnotation(MY_ANNOTATION)) return emptySet()
        return setOf(Name.identifier("generatedMethod"))
    }

    override fun generateFunctions(
        callableId: CallableId, context: MemberGenerationContext?
    ): List<FirNamedFunctionSymbol> {
        return listOf(buildFunctionSignature(callableId, context, MyKey))
    }
}
```

## Two-Pass IR Lowering

To prevent symbol resolution crashes when generating forward-referencing members (e.g., Class A referencing Class B's generated methods before Class B is lowered), utilize a two-pass architecture.

```kotlin
class MyIrExtension : IrGenerationExtension {
    override fun generate(moduleFragment: IrModuleFragment, ctx: IrPluginContext) {
        // Pass 1: Generate empty declaration stubs to populate the symbol table
        moduleFragment.files.forEach { StubGenerator(ctx).runOnFileInOrder(it) }
        // Pass 2: Fill method bodies now that all symbols are resolvable
        moduleFragment.files.forEach { BodyGenerator(ctx).runOnFileInOrder(it) }
    }
}
```

## Incremental Compilation & Daemon Safety

*   **Daemon Safety**: The K2 compiler daemon executes compilations concurrently. Never use static mutable singletons. Wrap all compilation-level state in `InheritableThreadLocal`.
*   **IC Limitation**: Changes inside lambda bodies do not modify the ABI and may be missed by incremental builds. Force aggregator task recompilation where required.

```kotlin
object PluginState {
    val threadCollector = InheritableThreadLocal<MessageCollector?>()
    @Volatile var fallback: MessageCollector = MessageCollector.NONE
    val effective get() = threadCollector.get() ?: fallback
}
```

## Cross-Module Discovery

Since plugins cannot scan dependencies inside pre-compiled JARs, generate synthetic **hint functions** during compilation. Downstream modules can then query these signatures via `pluginContext.referenceFunctions()` to discover annotated targets.

## Testing & Debugging

Verify compilation behavior using golden file testing (`.fir.txt` and `.fir.ir.txt` snapshots) and JVM box tests.

*   `-Xverify-ir`: Enable during development to check IR structure (type mismatches, scope leaks).
*   `-Xphases-to-dump-before=<Phase>`: Dump the IR AST prior to a lowering phase to debug transforms.

Debugging and Testing configurations: [testing-debugging.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/testing-debugging.md)

## Kotlin 2.4.0 Compatibility

Ensure generated code complies with Kotlin 2.4.0 features and compiler strictness:
*   **Context parameters**: Handle implicit parameter resolution and explicit context args.
*   **Explicit backing fields**: Process inline `field` keywords in property accessors.
*   **Annotation targets**: Prioritize `param` > `property` > `field` defaults.
*   **getValue/setValue**: Enforce strict parameter counts (2 for get, 3 for set).
*   **Jakarta nullability**: Null-check Jakarta annotations during code generation.

Comprehensive breaking changes and features guide: [kotlin-2-4-compat.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/kotlin-2-4-compat.md)

<constraints>
When helping developers with Kotlin K2 plugins, you must enforce the following format requirements:
- Always require cross-referencing [plugin-blueprint.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/plugin-blueprint.md) for module setup, CLI options, and service configuration.
- Always require cross-referencing [optimization-patterns.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/optimization-patterns.md) for lazy scanning, daemon-parallel safety, and session caching.
- Always require cross-referencing [kotlin-2-4-compat.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/kotlin-2-4-compat.md) for 2.4.0 migrations.
- Always require cross-referencing [testing-debugging.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/testing-debugging.md) for troubleshooting test failures.
- Always require cross-referencing [real-world-patterns.md](file:///Users/jsanjaya/Projects/skills/kotlin-k2-expert/references/real-world-patterns.md) forInsertKoin K2 patterns.

All target configurations should be verified using the `@file:line` syntax and tested using specific compiler verification flags. Output must be wrapped in XML tags only.
</constraints>
