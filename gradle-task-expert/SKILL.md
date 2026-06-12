---
name: gradle-task-expert
description: Expert guidance for authoring and configuring Gradle tasks using Groovy DSL and Kotlin DSL (KTS) for Gradle 9.5.1 with Configuration Cache, up-to-date checks, and input/output modeling. Make sure to use this skill whenever the user asks about registering Gradle tasks, configuring task actions, resolving configuration cache violations, migrating from eager to lazy task APIs, declaring inputs/outputs with properties and providers, or setting up task dependency/ordering relationships, even if they don't explicitly name 'gradle-task-expert'.
---

# Gradle Task Expert

<instructions>
Provide design, configuration, and debugging assistance for Gradle task authoring and task registration under Groovy DSL and Kotlin DSL (KTS). Ensure compliance with Gradle 9.5.1+ standards, task configuration avoidance, and configuration cache rules. Check the references index and guide routing below to target specific details.
</instructions>

<version_matrix>

## Gradle Task Lifecycle & Compatibility (2026)

| Concept | Modern / Gradle 9.5.1+ | Legacy / Outdated | Recommendation |
|---|---|---|---|
| **Registration** | `tasks.register("name")` (Lazy) | `tasks.create("name")` or `task name` (Eager) | **Lazy ONLY** for Configuration Avoidance. |
| **API Target** | `Property<T>`, `DirectoryProperty`, `RegularFileProperty` | Plain Java type fields (`File`, `String`, etc.) | **Managed Properties** for provider chaining. |
| **Caching** | `@CacheableTask` or `@DisableCachingByDefault` | No caching annotations | Custom tasks **must** declare one or the other. |
| **CLI Verification** | `--scan` or `tasks --provenance` | Custom diagnostic print statements | Leverage Gradle's built-in troubleshooting. |

</version_matrix>

<syntax_transform>

## Task Registration & Configuration Avoidance

Do not use legacy eager APIs (`tasks.create()`, `tasks.all`, `tasks.getByName()`). Always register tasks lazily and wire them using the Provider API:

| Eager API (Avoid) | Lazy API (Prefer) | Why |
|---|---|---|
| `tasks.create("foo") { ... }` | `tasks.register("foo") { ... }` | Avoids realizing task until needed. |
| `tasks.getByName("foo")` | `tasks.named("foo")` | Defers task lookup. |
| `tasks.all { ... }` | `tasks.configureEach { ... }` | Does not trigger instant task realization. |
| `tasks.withType(Test) { ... }` | `tasks.withType(Test).configureEach { ... }` | Keeps container configuration lazy. |

</syntax_transform>

<reference_index>

## Reference Index

- [basics.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/basics.md)
  - Core task anatomy, lifecycle phases, lazy task registration APIs, TaskProvider, and Gradle 9.5.1 deprecations.
  - *Read when*: Understanding task lifecycle, implementing `DefaultTask`, or using Gradle 9.5.1+ features.
- [configuration-cache.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/configuration-cache.md)
  - Configuration cache rules, preventing `Project` instance leaks in task actions, lazily reading env/sys properties, secure secrets handling, and script-object capture via `onlyIf`/`doFirst`/`Provider.map {}` lambdas in `.gradle.kts`.
  - *Read when*: Fixing configuration cache violations, avoiding configuration-time execution, handling environment variables, or getting "cannot serialize Gradle script object references" errors.
- [inputs-outputs.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/inputs-outputs.md)
  - Managed properties, up-to-date checks, path sensitivity, Kotlin getter `@get:` requirements, incremental tasks via `InputChanges`, `SourceTask.source()` double-registration, `onlyIf` purity rules, and `val` shadowing of `Project` extension properties.
  - *Read when*: Declaring inputs/outputs, troubleshooting caching/incremental execution, modeling file parameters, or using `onlyIf` with side effects.
- [groovy-vs-kts.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/groovy-vs-kts.md)
  - Comprehensive comparison between Groovy and Kotlin DSL formats, type-safe task accessors, and migration rules.
  - *Read when*: Migrating build scripts from Groovy to Kotlin DSL, or writing task wiring in both languages.
- [testing-debugging.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/testing-debugging.md)
  - Unit testing tasks with `ProjectBuilder`, functional testing with TestKit (`GradleRunner`), and CLI debugging.
  - *Read when*: Writing automated tests for tasks or diagnosing execution/cache failures.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "How to migrate task from Groovy to KTS" or "tasks.register syntax differences" | [groovy-vs-kts.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/groovy-vs-kts.md) |
| "Configuration cache state could not be cached because Project instance leaked" | [configuration-cache.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/configuration-cache.md) |
| "Task output is not cacheable" or "How to define inputs and outputs" | [inputs-outputs.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/inputs-outputs.md) |
| "Kotlin getter annotations not picked up" or "Missing task properties" | [inputs-outputs.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/inputs-outputs.md) |
| "`source()` and `inputs.files()` both declared on same Detekt/SourceTask" | [inputs-outputs.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/inputs-outputs.md) |
| "Side effects in `onlyIf`" or "mkdirs / writeText inside onlyIf" | [inputs-outputs.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/inputs-outputs.md) |
| "`val rootDir` shadowing or `val projectDir` shadows Project extension" | [inputs-outputs.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/inputs-outputs.md) |
| "How to run command in task action for configuration cache" | [configuration-cache.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/configuration-cache.md) |
| `"cannot serialize Gradle script object references"` error | [configuration-cache.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/configuration-cache.md) |
| "`onlyIf {}` or `doFirst {}` in `.gradle.kts` breaks CC" | [configuration-cache.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/configuration-cache.md) |
| "`Provider.map {}` in script breaks configuration cache" | [configuration-cache.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/configuration-cache.md) |
| "How to write a functional test using GradleRunner or TestKit" | [testing-debugging.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/testing-debugging.md) |
| "Gradle 9.5.1 task deprecations or Task.doFirst / Task.doLast smells" | [basics.md](file:///Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/basics.md) |

</routing_table>

<constraints>
- All reference files and linked documentation **must** be referenced using their absolute file:/// paths under `/Users/jsanjaya/.gemini/config/skills/gradle-task-expert/references/`.
- Tasks **must** be registered lazily using `register` or `registering`, and wired lazily via `flatMap` / `map` / `set` using the Provider API.
- Do **not** allow imperative tasks without type definitions (`tasks.register("foo") { doLast { ... } }`) unless it is a quick prototyping step. Custom business logic must live in abstract classes extending `DefaultTask`.
- Do **not** leak `Project` references in task actions, and do not call build-logic execution routines during the configuration phase.
- Custom tasks must explicitly declare cacheability: `@CacheableTask` or `@DisableCachingByDefault(because = "...")`.
</constraints>
