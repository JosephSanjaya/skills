---
name: gradle-convention-expert
description: Expert guidance for Gradle precompiled script plugins, shared convention build-logic, composite included builds, and AGP 9.0+ migrations. Use when designing build architecture, creating convention plugins (*.gradle.kts), resolving Version Catalog access from plugins, fixing classpath collisions, or optimizing configuration cache. Triggers on gradle convention, precompiled script, build-logic, composite build, libs.versions.toml in plugin, ClassCastException gradle, gradle performance.
---

# Gradle Convention Expert

<instructions>
Provide design, configuration, and debugging assistance for Gradle precompiled script plugins, shared convention build-logic, composite included builds, and AGP 9.0+ migrations. Check the references index and guide routing below to target specific details.
</instructions>

<version_matrix>

## Baseline Compatibility Matrix (2026)

| Tool / Framework | Min for AGP 9.0+ | Notes |
|---|---|---|
| Gradle | `9.1.0`+ (9.4.1+ recommended for AGP 9.2+) | Required Gradle wrapper version |
| JDK | `17` minimum | Java Toolchain target |
| Kotlin (KGP) | `2.2.10`+ | Compiler runtime alignment |
| Android Gradle Plugin (AGP) | `9.0.0`+ | Built-in Kotlin enabled by default |

</version_matrix>

<file_scopes>

## File Naming & Target Scopes

Precompiled scripts compile directly into JVM classes. Suffix determines receiver context:

| File Suffix | Compiled Receiver Target | Primary Use Case |
|---|---|---|
| `.gradle.kts` | `Plugin<Project>` | Module configuration (Java/Android toolchains, dependencies). |
| `.settings.gradle.kts` | `Plugin<Settings>` | Composite builds, centralizing catalogs, project structure. |
| `.init.gradle.kts` | `Plugin<Gradle>` | Global environment setups, corporate repos, proxy servers. |

Script namespace derived from package declaration and directory structure.
* File: `src/main/kotlin/my/org/conventions/android-lib.gradle.kts`
* Header: `package my.org.conventions`
* Exposed Plugin ID: `my.org.conventions.android-lib`

</file_scopes>

<syntax_transform>

## Syntax Transformation (Imperative to Composable)

Eliminate imperative abstract base classes and global static singletons. Use clean, declarative, type-safe DSL blocks:

| Imperative API (`Plugin<Project>`) | Composable Script Plugin (`.gradle.kts`) |
|---|---|
| `project.pluginManager.apply("com.android.library")` | `plugins { id("com.android.library") }` |
| `project.extensions.findByType(LibraryExtension::class.java)` | `android { ... }` |
| `project.tasks.register("myTask", MyTask::class.java)` | `tasks.register<MyTask>("myTask")` |
| `project.dependencies.add("implementation", "org:lib:1.0")` | `dependencies { implementation("org:lib:1.0") }` |

</syntax_transform>

<reference_index>

## Reference Index

- [architecture.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/architecture.md)
  - Shared build-logic module design, convention layers, source sharing via Git submodules, root-project convention plugin pattern, and replacing `alias(libs.plugins.X)` with convention plugin IDs.
  - *Read when*: Structuring composite builds, dividing convention plugins into layers, linking plugins across repos, or applying a convention plugin to the root project.
- [version-catalog.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/version-catalog.md)
  - Resolving the Version Catalog bootstrapping paradox (Issue #15383) via classpath injection, string-based lookup, or plugin-owned catalogs (Issue #36337).
  - *Read when*: Resolving `Unresolved reference: libs` inside convention plugins or configuring central catalogs.
- [performance.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/performance.md)
  - Incremental snapshotting, configuration caching compliance, global UTF-8 encoding, and classloader isolation.
  - *Read when*: Fixing configuration cache violations, optimizing build times, or resolving ClassCastExceptions.
- [agp-migration.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/agp-migration.md)
  - Upgrades for AGP 9.0+/Kotlin 2.2+, built-in Kotlin support changes, API replacements, and toolchain constraints.
  - *Read when*: Upgrading projects to AGP 9.0+, removing redundant `kotlin-android` plugins, or configuring built-in Kotlin compiler options.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "Unresolved reference: libs" or "Cannot resolve libs in build-logic" | [version-catalog.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/version-catalog.md) |
| "Unable to load class com.android.build.api.dsl.ApplicationExtension" or ClassCastException | [performance.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/performance.md) |
| "The org.jetbrains.kotlin.android plugin is no longer required for Kotlin support since AGP 9.0" | [agp-migration.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/agp-migration.md) |
| "Cannot add extension with name 'kotlin', as there is an extension already registered" | [agp-migration.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/agp-migration.md) |
| "Configuration cache state could not be cached because Project instance leaked" | [performance.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/performance.md) |
| "How to share conventions across distinct corporate repositories" | [architecture.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/architecture.md) |
| "Convention plugin applied to root project" or "repo-wide tasks in buildSrc" | [architecture.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/architecture.md) |
| "Replace alias(libs.plugins.X) with convention plugin" or "no version needed in root plugins block" | [architecture.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/architecture.md) |
| "How to scaffold a modular preconfigured build-logic directory" | See Automation Scripts section below |

</routing_table>

<automation_scripts>

## Automation Scripts

```bash
# Scaffold a modular, preconfigured 'build-logic' composite structure:
python3 /Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/scripts/scaffold_build_logic.py [target-project-path]
```

</automation_scripts>

<constraints>
- All reference files and linked documentation **must** be referenced using their absolute file:/// paths under `/Users/jsanjaya/.gemini/config/skills/gradle-convention-expert/references/`.
- Always verify AGP 9.0+ built-in Kotlin constraints and ensure `org.jetbrains.kotlin.android` is **only** applied in legacy AGP 8.x environments.
- Developers **should** favor lazy configuration (e.g. `tasks.register`) and avoid leaking `Project` references in task actions to maintain Configuration Cache compatibility.
</constraints>
