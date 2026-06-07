---
name: koin-expert
description: "Koin Compiler Plugin (K2 native) expert for Kotlin DI. Triggers when: writing/reviewing Kotlin DI with Koin; setting up @Single/@Factory/@KoinViewModel/@Module/@ComponentScan/@KoinApplication/@Scope/@Scoped/@Provided annotations; migrating KSP to the native compiler plugin; configuring multi-module or KMP Koin; debugging NoDefinitionFoundException or silent bean-drop bugs; asking about compile-time safety levels A2/A3/A4; Koin scoping, performance, or memory management. NOT for KSP-only or Hilt/Dagger questions."
---

# Koin Expert (K2 Compiler Plugin Edition)

<instructions>
Provide design, configuration, and debugging assistance for Koin dependency injection in Kotlin/JVM, Android, and KMP projects, specifically targeting the native K2 compiler plugin stack.
</instructions>

## Version Compatibility Matrix (2026)

| Artifact | Version | Notes |
|---|---|---|
| `koin-core` + `koin-annotations` | `4.2.0`+ (must match exactly) | Recommended stable version |
| `io.insert-koin.compiler.plugin` | `1.0.0-RC2`+ | Native K2 compiler plugin (no KSP) |
| Kotlin | `2.3.20`+ (K2 enabled) | Lack of binary compatibility across minor versions |
| Gradle | `8.0`+ | Required for latest toolchain |

## KSP vs K2 Compiler Plugin Comparison

| Feature | Legacy KSP | K2 Compiler Plugin |
|---|---|---|
| **Backend engine** | Google KSP | K2 FIR + IR native transformer |
| **Code Generation** | Generates visible `.kt` source files | In-memory direct IR transformation (no generated files) |
| **KMP Configuration** | Verbose (~25 lines per source set) | Apply plugin to Gradle, done |
| **Safety Check** | Runtime `checkModules()` / `verify()` | Compile-time A2/A3/A4 validation |
| **Kotlin Requirement** | `1.9.x` - `2.1.x` | `2.3.x`+ (K2 compiler) |

## Gradle Configuration Summary

Apply the plugin and dependencies:
```kotlin
// build.gradle.kts
plugins {
    id("io.insert-koin.compiler.plugin") version "1.0.0-RC2"
}

dependencies {
    implementation("io.insert-koin:koin-core:4.2.0")
    implementation("io.insert-koin:koin-annotations:4.2.0")
    // Required if @KoinViewModel or @KoinWorker is used:
    implementation("io.insert-koin:koin-core-viewmodel:4.2.0")
    implementation("io.insert-koin:koin-android-workmanager:4.2.0")
}
```

Configure compiler extension options in the aggregator `build.gradle.kts` module:
```kotlin
koinCompiler {
    compileSafety = true       // Enable compile-time validation (default: true)
    userLogs = true            // Show component detection during compilation
    debugLogs = false          // Verbose internal plugin debugging logs
    unsafeDslChecks = true     // Validate create() is the only instruction in lambdas
    skipDefaultValues = true   // Skip validation for parameters with default arguments
}
```

## Annotation APIs

```kotlin
@Single / @Singleton                     // App-scoped singleton
@Factory                                 // New instance per injection site
@KoinViewModel                           // org.koin.core.annotation.KoinViewModel (not android.annotation)
@Module + @ComponentScan("com.pkg")      // Define a local module configuration
@KoinApplication(modules = [AppModule::class]) // Type-safe graph entry point
@Named("key")                            // Qualifier annotation
@Provided                                // Skips local A2 check, deferred to app root validation (A3)
@Scope(MarkerClass::class) + @Scoped     // Custom scope (always use MarkerClass class, never raw strings)
```

## Compile-Time Safety Validation (A2 / A3 / A4)

- **A2 (Module Level)**: Validates local dependency graphs, checks missing parameters, qualifiers, and scope violations.
- **A3 (Application Level)**: Executed at the `@KoinApplication` entry point. Validates the full unified graph.
- **A4 (Call-Site Level)**: Checks runtime `inject()`, `get()`, or `koinViewModel()` calls against the compiled graph.

## Troubleshooting Incremental Compilation (IC) Catch-22

If you modify lambda bodies or internal bindings without changing class signatures (ABI), Kotlin's Incremental Compilation might mark the aggregator module as up-to-date and skip the A3 graph assembly, causing runtime `NoDefinitionFoundException` errors.

**Workarounds**:
1. **Disable multiplatform/project incremental compilation** in `gradle.properties`:
   ```properties
   kotlin.incremental.multiplatform=false
   # or
   kotlin.incremental=false
   ```
2. **Perform clean builds** when modifying dependency bindings inside dependent modules:
   ```bash
   ./gradlew clean assembleDebug
   ```

## Custom Scoping Guidelines

- **Always use a Marker Class** for custom scopes:
  ```kotlin
  class SessionFlowScope // Marker class
  
  @Scope(SessionFlowScope::class)
  @Scoped
  class SessionCache
  ```
- Avoid string-named scopes in annotations (e.g. `@Scope(name = "scope_id")`) as they can lead to runtime definition drops when combined with explicit bindings.
- ViewModels must **never** hold references to `@ActivityScope` or `@FragmentScope` components to prevent memory/activity leaks.

<constraints>
- Always verify Kotlin, Koin, and plugin versions against the compatibility matrix.
- Ensure all Gradle, DI configuration, and architectural guidance matches the details in the reference documentation files:
  * [gradle-setup.md](file:///Users/jsanjaya/Projects/skills/koin-expert/references/gradle-setup.md) - Full version catalogs, build setups, KMP configuration, and plugin options.
  * [migration.md](file:///Users/jsanjaya/Projects/skills/koin-expert/references/migration.md) - Step-by-step checklist to migrate from KSP to the K2 Compiler Plugin.
  * [multi-module.md](file:///Users/jsanjaya/Projects/skills/koin-expert/references/multi-module.md) - Cross-module routing, Clean Architecture `@Provided` patterns, and KMP expect/actual overrides.
  * [scoping.md](file:///Users/jsanjaya/Projects/skills/koin-expert/references/scoping.md) - Scope hierarchy, lifecycle management, and preventing memory leaks.
  * [resources.md](file:///Users/jsanjaya/Projects/skills/koin-expert/references/resources.md) - Links to official documentation, repository releases, and relevant issue trackers.
- Always write Kotlin DSL build scripts and Kotlin source code inside complete code blocks.
- Explicitly check for compiler plugin compileSafety options when diagnosing dependency issues.
</constraints>
