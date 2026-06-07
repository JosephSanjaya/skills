# Migration Guide: KSP to Koin Compiler Plugin

## Migration Checklist

1. **Update Toolchain**: Set Kotlin to version `2.3.20`+ (K2 compiler is required) and Gradle to `8.0`+.
2. **Remove KSP Plugin**: Remove the KSP plugin application from each module's `build.gradle.kts`:
   ```kotlin
   // Remove:
   alias(libs.plugins.ksp)
   ```
3. **Remove KSP Dependencies**: Remove `koin-ksp-compiler` dependencies from all configurations:
   ```kotlin
   // Remove:
   ksp(libs.koin.ksp.compiler)
   // or: ksp("io.insert-koin:koin-ksp-compiler:...")
   ```
4. **Align Dependency Versions**: Keep `koin-annotations` version aligned exactly with `koin-core`:
   ```toml
   koin = "4.2.0"                  # Shared across core & annotations
   koin-plugin = "1.0.0-RC2"       # Plugin version (managed separately)
   ```
5. **Apply Koin Compiler Plugin**: Add the plugin alias to your module build configurations:
   ```kotlin
   plugins {
       alias(libs.plugins.koin.compiler)
   }
   ```
6. **Update ViewModel Annotations**: Correct imports for `@KoinViewModel` package definitions:
   ```kotlin
   // Old (KSP):
   import org.koin.android.annotation.KoinViewModel
   
   // New (Compiler Plugin):
   import org.koin.core.annotation.KoinViewModel
   ```
7. **Type-Safe App Initialization**: Use reified generic type parameters on `startKoin` instead of referencing generated classes:
   ```kotlin
   // Old (KSP):
   import org.koin.ksp.generated.*
   startKoin { modules(AppModule().module) }
   
   // New (Compiler Plugin):
   startKoin<ApplicationGraph> {
       androidLogger()
       androidContext(this@MainApplication)
   }
   ```
8. **Clean Generated Imports**: Search for and delete KSP generated code package declarations:
   ```bash
   grep -r "import org.koin.ksp.generated" . --include="*.kt"
   ```
9. **Purge Build Caches and Rebuild**: Clean KSP outputs and run a fresh compilation:
   ```bash
   rm -rf build/generated/ksp
   ./gradlew clean assembleDebug
   ```

## Common Migration Pitfalls

| Diagnostic Issue | Cause | Resolution |
|---|---|---|
| `Unresolved reference: module` on `AppModule().module` | KSP extension property generation is gone. | Use `startKoin<AppGraph>()` syntax at app entry points, or call compile-generated `AppModule.module()` extension functions. |
| `No type arguments expected` or unresolved `module` on `module<T>()` | Reified `module<T>()` returns `Unit` and is restricted to `KoinApplication` scope. | Call the compiler-generated extension function `T.module()` to return the compiled `Module` object dynamically (e.g., for `listOf(T.module())` or `loadKoinModules`). |
| Missing `koin-core-viewmodel` dependency error during FIR build phase. | `@KoinViewModel` class is present, but compiler validation plugin lacks runtime types. | Add `implementation(libs.koin.core.viewmodel)` to the module's dependencies. |
| `NoDefinitionFoundException` after making changes in incremental builds. | Incremental Compilation (IC) Catch-22: A3 checks skipped. | Set `kotlin.incremental=false` in `gradle.properties`, or run `./gradlew clean`. |
| Unresolved `@KoinViewModel` reference. | Legacy package import. | Replace `import org.koin.android.annotation.KoinViewModel` with `import org.koin.core.annotation.KoinViewModel`. |

## DSL Changes (Legacy vs Compiler-Enhanced DSL)

The native plugin lets you auto-wire constructors in DSL without reflection or verbose parameters:

```kotlin
// Legacy Koin DSL (Manual constructor mapping):
single { MyService(get(), get()) }
singleOf(::MyService) // (uses reflection)

// Compiler-Enhanced DSL (Auto-wired at compile time):
single<MyService>()            // Compiler auto-wires all dependencies
factory { create(::MyService) } // Auto-wires custom builder blocks
```

Ensure you update DSL package imports:
```kotlin
// Legacy:
import org.koin.core.module.dsl.singleOf

// Compiler-Enhanced:
import org.koin.plugin.module.dsl.single
import org.koin.plugin.module.dsl.create
```
