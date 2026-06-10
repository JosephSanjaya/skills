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
