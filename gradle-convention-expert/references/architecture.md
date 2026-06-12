# Gradle Shared Build-Logic Architecture

## Included Build (build-logic) vs buildSrc

| Dimension | Legacy buildSrc | Included Build (build-logic) |
|---|---|---|
| **Classpath Coupling** | High. Automatically injected into root project classpath. | Isolated. Scoped/loaded only upon targeted request. |
| **Caching Boundaries** | Poor. Any changes invalidate root build script caches. | Excellent. Changes localized; minimal recompilation cascade. |
| **CLI Flexibility** | Hard-coupled. Cannot bypass or exclude. | High. Can open/develop/test in isolation. |
| **Multi-Repo Portability** | Hard-coded to single multi-project build structure. | Fully portable. Linkable to multiple projects via Git submodules. |

## Convention Layout Strategy

Deconstruct monolithic base setups into discrete layers:

1. **Base Conventions:** Common setup for all modules. Enforces Java Toolchain, global compiler args (`-Xjvm-default=all`), default code-quality/checkstyle tools.
2. **Feature Conventions:** Specific capabilities:
   - `kotlin-jvm-conventions`: Kotlin compilation, warning configuration.
   - `kotlin-android-conventions`: Android Kotlin compilation, target SDK setups.
   - `testing-conventions`: Unit test suites, mock configurations.
   - `publishing-conventions`: Maven publishing configuration.
3. **Check Conventions:** Maintainability/styling enforcement: Detekt, Spotless, Dependency Analysis.
4. **Module-Type Conventions:** Aggregates layers into ready-to-use bundles:
   - `library-conventions`: Core JVM library configurations.
   - `android-library-conventions`: Android Library configurations.
   - `android-application-conventions`: Android Application configurations.

---

## Root-Project Convention Plugin Pattern

Not all convention plugins target submodules. A convention plugin applied to the **root project** is the correct place for tasks that operate across the whole repo — git-scoped formatting, cross-module reports, or aggregate CI tasks.

The plugin ID is derived from the filename: `buildSrc/src/main/kotlin/tool/tool.detekt-autoformat.gradle.kts` → `id("tool.detekt-autoformat")`.

Key constraints when writing a root-project convention plugin:
- Reference files via `rootProject.layout.projectDirectory.file(...)` not `layout.projectDirectory.file(...)` (same project here, but explicit avoids confusion if plugin is reused).
- Avoid `project(":some:module")` dependencies — root-applied plugins run before subproject evaluation is complete.
- Tasks registered here appear in the root project task list, not in any submodule.

### Example: Root Plugin Applying detekt + Registering Repo-Wide Tasks
```kotlin
// buildSrc/src/main/kotlin/tool/tool.detekt-autoformat.gradle.kts
plugins { id("io.gitlab.arturbosch.detekt") }

val libs = versionCatalogs.find("libs")
dependencies {
    detektPlugins(libs.flatMap { it.findLibrary("detekt-formatting") }.get())
}

tasks.register<io.gitlab.arturbosch.detekt.Detekt>("detektAutoFormatDiff") {
    notCompatibleWithConfigurationCache("reads git diff at execution time")
    autoCorrect = true
    config.setFrom(rootProject.layout.projectDirectory.file("config/quality/detekt/detekt-config.yml"))
    // ...
}
```

Applied in root `build.gradle.kts`:
```kotlin
plugins {
    id("tool.detekt-autoformat") // no version — buildSrc is on classpath automatically
}
```

---

## Replacing `alias(libs.plugins.X)` with a Convention Plugin ID

When a convention plugin internally applies the same plugin that was previously declared in the root `plugins {}` block via `alias(libs.plugins.X)`, the alias can be replaced with the convention plugin ID. No version is needed because buildSrc plugins are on the root classpath.

```kotlin
// Before — root build.gradle.kts
plugins {
    alias(libs.plugins.detekt)         // applies detekt at version from TOML
}
dependencies {
    detektPlugins(libs.detekt.formatting) // detektPlugins config in root
}

// After — root build.gradle.kts
plugins {
    id("tool.detekt-autoformat") // convention plugin applies detekt internally
}
// dependencies block removed — convention plugin owns detektPlugins declaration
```

Gradle applies plugins idempotently — if the convention plugin applies `id("io.gitlab.arturbosch.detekt")` and something else also applies it, there is no double-application error. The plugin is applied once and the extension is shared.

---

## Git Submodule Sharing Pattern

For sharing conventions across distinct corporate repositories without intermediate binary releases:

1. Add convention repo as Git Submodule under `/build-logic`:
   ```bash
   git submodule add <repo-url> build-logic
   ```
2. Register in consumer `settings.gradle.kts`:
   ```kotlin
   pluginManagement {
       includeBuild("build-logic")
   }
   ```

### Constraints:
* **Unique Build Paths:** No two included builds can share directory layouts.
* **No Namespace Overlaps:** Paths defined inside included build must not conflict with root paths.
