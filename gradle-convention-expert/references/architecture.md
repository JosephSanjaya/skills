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
