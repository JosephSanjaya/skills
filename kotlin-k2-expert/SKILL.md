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
Provide expert guidance on Kotlin K2 compiler plugin development, FIR/IR phases, optimization, and compatibility. Use the relative reference files below to solve specific implementation or debugging requests.
</instructions>

<decision_matrices>

## FIR Extension Point Selection

| Extension Class | Phase | Purpose |
|---|---|---|
| `FirSupertypeGenerationExtension` | Supertype Resolution | Modify/inject supertypes |
| `FirStatusTransformerExtension` | Status Resolution | Modify visibility, modality, or inline status |
| `FirDeclarationGenerationExtension` | Callable Generation | Lazily generate synthetic members/classes |
| `FirTypeAttributeExtension` | Annotation Args | Process type attributes/annotations |
| `FirAdditionalCheckersExtension` | Diagnostics | Implement custom compile-time checkers |
| `IrGenerationExtension` | IR Lowering | Backend transforms, bytecode generation |

</decision_matrices>

<reference_index>

## Reference Index

- [plugin-blueprint.md](references/plugin-blueprint.md)
  - Full three-module structure, registration files, `CompilerPluginRegistrar`, `FirDeclarationGenerationExtension` signature creation, CLI options processing.
  - *Read when*: Setting up a new plugin, registering CLI args, building first generators.
- [optimization-patterns.md](references/optimization-patterns.md)
  - Lazy provider generation, Session component caching, daemon-parallel safety, force aggregator re-evaluation.
  - *Read when*: Optimizing performance, debugging concurrent builds, fixing stale cache issues.
- [kotlin-2-4-compat.md](references/kotlin-2-4-compat.md)
  - Stricter getValue/setValue delegates, context parameters, explicit backing fields, Jakarta nullability checks, default annotation targets.
  - *Read when*: Migrating to Kotlin 2.4.0+, debugging generated code compilation errors.
- [testing-debugging.md](references/testing-debugging.md)
  - Compiler test infrastructure, box and diagnostics tests, golden snapshot files, verification flags (`-Xverify-ir`, `-Xphases-to-dump-before`).
  - *Read when*: Writing unit/box tests, debugging IR trees, checking AST structure.
- [real-world-patterns.md](references/real-world-patterns.md)
  - Battle-tested design patterns from the InsertKoin compiler plugin, including multi-phase IR transforms and hint functions.
  - *Read when*: Designing large scale compiler plugins, doing cross-module symbol discovery.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "Unresolved reference" in generated code (compile-time) | [testing-debugging.md](references/testing-debugging.md) |
| Symbol table corruption or crash during IR lowering | [testing-debugging.md](references/testing-debugging.md) |
| Volatile singletons overwritten in concurrent builds | [optimization-patterns.md](references/optimization-patterns.md) |
| Missing generated symbols in pre-compiled downstream JARs | [optimization-patterns.md](references/optimization-patterns.md) |
| Delegate getValue/setValue compilation failure in 2.4.0 | [kotlin-2-4-compat.md](references/kotlin-2-4-compat.md) |
| Eager classpath scanning slowing down compilation | [optimization-patterns.md](references/optimization-patterns.md) |

</routing_table>

<constraints>
When helping developers with Kotlin K2 plugins, you must enforce the following format requirements:
- Always require lazy provider APIs in FIR generation (no eager scanning).
- Always require that all generated code handles Kotlin 2.4.0 delegate constraints and context parameters.
- Always require that IR lowering implements the two-pass (stubs before bodies) pattern to prevent symbol errors.
- Always require that volatile compilation-level state uses ThreadLocal mechanisms for parallel compiler daemon safety.
- Output should be structured clearly and only contain verified compiler plugin configurations.
</constraints>
