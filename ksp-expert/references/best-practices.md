# KSP Best Practices & Optimization

## Coding Best Practices

### 1. Avoid Eager Type Resolution
- `KSTypeReference.resolve()` = main cost center. Resolves semantic type info.
- **Do**: Filter declarations by simple name, package, or structures first. Resolve ONLY when absolutely needed.
- **Don't**: Call `.resolve()` on all annotation types or members blindly.

### 2. Annotation Scans vs File Scans
- **Do**: Use `Resolver.getSymbolsWithAnnotation()`. Target specific symbols.
- **Don't**: Use `Resolver.getAllFiles()`. Eagerly processes everything, destroys compile avoidance, slow.

### 3. Precise `Dependencies` Setup
- Incrementality depends on `Dependencies` map.
- **Isolating Output** (`aggregating = false`):
  - Associated with specific source file (`KSFile`).
  - Output regenerated only if that source file changes.
  - Setup: `Dependencies(aggregating = false, sourceFile)`
- **Aggregating Output** (`aggregating = true`):
  - Combined output (e.g., lookup index).
  - Output regenerated if any source files change or new files added.
  - Setup: `Dependencies(aggregating = true, sourceFile1, sourceFile2)`
- **All Files**: `Dependencies.ALL_FILES`. Disables incrementality. Do not use.

### 4. Deterministic Output
- Symbol resolution order is non-deterministic.
- **Do**: Sort symbols explicitly (e.g. by FQN) before writing output. Prevents compiler cache misses.

### 5. Caching Constraints
- **Do**: Cache plain data (Strings, primitives, custom data classes) between rounds.
- **Don't**: Cache `KS*` symbol objects (e.g. `KSClassDeclaration`, `KSType`).
  - Symbols are invalid in subsequent rounds.
  - Causes PSI-lifetime errors under KSP2.

### 6. Annotation Parameter Reading under KSP2
- KSP2 beta has bugs with proxy-backed annotation parameter reading (especially nested annotations / defaults).
- **Do**: Read arguments manually via `KSAnnotation.arguments`:
  ```kotlin
  val value = annotation.arguments.firstOrNull { it.name?.asString() == "paramName" }?.value
  ```

### 7. Nullable Source Files in Dependencies
- The containing file (`containingFile`) of a symbol is nullable (e.g. if the symbol is from a precompiled dependency/classpath).
- Passing a nullable `KSFile?` directly into `Dependencies(aggregating = false, ...)` will cause a compilation error.
- **Do**: Safely wrap the nullable `KSFile` using a helper:
  ```kotlin
  val sourceFile = classDec.containingFile
  val dependencies = sourceFile?.let { Dependencies(aggregating = false, it) }
      ?: Dependencies(aggregating = false)
  ```

### 8. Backing Fields in Generated Builders
- In Kotlin, if a property type is non-null (e.g., `String` or `Int`), we cannot initialize it to `null` in a generated Builder backing field.
- **Do**: Always declare backing fields as nullable in the generated Builder (e.g. `String?` or `Int?`) initialized to `null`. In the builder's setter method, accept the correct type (without nullability if it's non-null), and in the `build()` method, use `requireNotNull()` or `checkNotNull()` to assert that the value was provided:
  ```kotlin
  // Generated Builder Backing Field:
  private var name: kotlin.String? = null
  // Generated Builder Setter:
  fun name(name: kotlin.String) = apply { this.name = name }
  // Generated Builder Build Method:
  fun build() = User(name = requireNotNull(name) { "name must not be null" })
  ```

### 9. Multi-Round Processing and State/Round Guards
- **Don't**: Use a private state variable (e.g. `private var invoked = false`) to exit the `process` method after the first round.
- **Why**: If other processors generate code in subsequent rounds that matches your target annotations, your processor will fail to run on those newly generated files.
- **Do**: Always process new symbols returned in the current round. `Resolver.getSymbolsWithAnnotation()` naturally only returns new or deferred symbols for the current round. Return any unresolved symbols (symbols that fail validation via `validate()`) to defer them to the next round.

## Gradle Build Optimization

- **Hilt Aggregating Task**: Android builds using Hilt must enable aggregating task:
  ```kotlin
  hilt {
      enableAggregatingTask = true
  }
  ```
  Isolates Hilt compilation tasks, improves incremental build speed.
- **Room Kotlin Codegen**: Enable Kotlin code generation for Room:
  ```kotlin
  ksp {
      arg("room.generateKotlin", "true")
  }
  ```
  Speeds up compilation by skipping Java stub generation.
- **Build Caching**:
  - Keep processor path off compile classpath (use `ksp` configuration).
  - Use Room Gradle plugin (`schemaDirectory(...)`) for reproducible build cache results.
