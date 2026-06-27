---
name: koin-expert
description: "Koin Compiler Plugin (K2 native) expert for Kotlin DI. Triggers when: writing/reviewing Kotlin DI with Koin; setting up @Single/@Factory/@KoinViewModel/@Module/@ComponentScan/@KoinApplication/@Scope/@Scoped/@Provided annotations; migrating KSP to the native compiler plugin; configuring multi-module or KMP Koin; debugging NoDefinitionFoundException or silent bean-drop bugs; asking about compile-time safety levels A2/A3/A4; Koin scoping, performance, or memory management. NOT for KSP-only or Hilt/Dagger questions."
---

# Koin Expert (K2 Compiler Plugin Edition)

<instructions>
Provide design, configuration, and debugging assistance for Koin dependency injection in Kotlin/JVM, Android, and KMP projects, specifically targeting the native K2 compiler plugin stack. Check the reference files in the reference index below for detailed setups, migration steps, and scoping rules.
</instructions>

<version_matrix>

## Version Compatibility Matrix (2026)

| Artifact | Version | Notes |
|---|---|---|
| `koin-core` + `koin-annotations` | `4.2.0`+ (must match exactly) | Recommended stable version |
| `io.insert-koin.compiler.plugin` | `1.0.0-RC2`+ | Native K2 compiler plugin (no KSP) |
| Kotlin | `2.3.20`+ (K2 enabled) | Lack of binary compatibility across minor versions |
| Gradle | `8.0`+ | Required for latest toolchain |

</version_matrix>

<feature_comparison>

## KSP vs K2 Compiler Plugin Comparison

| Feature | Legacy KSP | K2 Compiler Plugin |
|---|---|---|
| **Backend engine** | Google KSP | K2 FIR + IR native transformer |
| **Code Generation** | Generates visible `.kt` source files | In-memory direct IR transformation (no generated files) |
| **KMP Configuration** | Verbose (~25 lines per source set) | Apply plugin to Gradle, done |
| **Safety Check** | Runtime `checkModules()` / `verify()` | Compile-time A2/A3/A4 validation |
| **Kotlin Requirement** | `1.9.x` - `2.1.x` | `2.3.x`+ (K2 compiler) |

</feature_comparison>

<compile_safety>

## Compile-Time Safety Validation (A2 / A3 / A4)

- **A2 (Module Level)**: Validates local dependency graphs, checks missing parameters, qualifiers, and scope violations.
- **A3 (Application Level)**: Executed at the `@KoinApplication` entry point. Validates the full unified graph.
- **A4 (Call-Site Level)**: Checks runtime `inject()`, `get()`, or `koinViewModel()` calls against the compiled graph.

</compile_safety>

<reference_index>

## Reference Index

- [gradle-setup.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/gradle-setup.md)
  - Full version catalogs, build setups, KMP sourceSet configuration, and compiler logging options. Resolves Incremental Compilation (IC) Catch-22 bugs.
  - *Read when*: Configuring Gradle plugins, managing versions, or resolving build cache issues.
- [migration.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/migration.md)
  - Step-by-step checklist to migrate from KSP to the K2 Compiler Plugin, viewmodel annotation package changes, and DSL upgrades.
  - *Read when*: Transitioning old Koin/KSP projects to the native K2 compiler plugin.
- [multi-module.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/multi-module.md)
  - Cross-module routing, Clean Architecture `@Provided` boundaries, dynamic feature module loading, and KMP expect/actual overrides.
  - *Read when*: Structuring multi-module projects, domain layer interfaces, or mocking test dependencies.
- [scoping.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/scoping.md)
  - Scope hierarchy, custom marker class scopes, scope lifecycle closing, early compiler plugin bugs, and preventing memory leaks.
  - *Read when*: Designing scoped structures (e.g. Session flow), managing Activity/Fragment lifecycles, or debugging silent drops.
- [resources.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/resources.md)
  - Links to official insert-koin documentation, GitHub release pages, and tracked issues for early plugin bugs.
  - *Read when*: Looking up API details or verifying active issue trackers.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "unresolved reference AppModule.module" or "AppModule().module removed" | [migration.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/migration.md) |
| "NoDefinitionFoundException after modifying dependency or lambda body" | [gradle-setup.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/gradle-setup.md) |
| "how to use reified module<T>() or compiled T.module() extension" | [migration.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/migration.md) |
| "missing dependency RemoteDataSource in core domain module A2 check" | [multi-module.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/multi-module.md) |
| "how to register expect/actual platform overrides with Koin compiler" | [multi-module.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/multi-module.md) |
| "scoped bean drop or missing definition at runtime with name parameter" | [scoping.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/scoping.md) |
| "memory leak in ViewModel using Activity or Fragment scoped dependencies" | [scoping.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/scoping.md) |
| "how to load and unload feature modules dynamically on onboarding exit" | [multi-module.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/multi-module.md) |

</routing_table>

<constraints>
- Always verify Kotlin, Koin, and plugin versions against the compatibility matrix.
- Ensure all Gradle, DI configuration, and architectural guidance matches the details in the reference documentation files.
- Always write Kotlin DSL build scripts and Kotlin source code inside complete code blocks.
- Explicitly check for compiler plugin `compileSafety` options when diagnosing dependency issues.
- All reference files and linked documentation must be referenced using their absolute file:/// paths under `/Users/jsanjaya/.gemini/config/skills/koin-expert/references/`.
- For infrastructure core modules (`:core:*:impl`), use `internal object` annotated with `@Module` + `@ComponentScan`; never expose DI bindings via public classes. See [multi-module.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/multi-module.md).
- For platform-specific bindings in KMP, always use `expect/actual` functions annotated `@Single` \u2014 never use runtime `if`-platform guards inside a shared provider. See [multi-module.md](file:///Users/jsanjaya/.gemini/config/skills/koin-expert/references/multi-module.md).
</constraints>
