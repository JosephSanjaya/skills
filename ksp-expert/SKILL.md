---
name: ksp-expert
description: "Google KSP and KSP2 expert for Kotlin annotation processing, Gradle setups, and multiplatform (KMP) code generation. Triggers when: writing or reviewing Kotlin Symbol Processing (KSP) code; creating a SymbolProcessor or SymbolProcessorProvider; configuring KSP in Gradle; migrating from kapt to KSP or KSP1 to KSP2; debugging compilation speed, incremental build regressions, or ClassCastException/PSI-lifetime errors in KSP; optimizing Kotlin code generation for Room, Hilt, or Ktorfit. Make sure to use this skill whenever the user mentions KSP, KSP2, symbol processing, kapt migration, or code generation in Kotlin."
---

# KSP Expert

<instructions>
Provide design, configuration, and debugging assistance for Google Kotlin Symbol Processing (KSP) in Kotlin JVM, Android, and KMP projects. Check the reference index below for detailed API differences, Gradle setup, best practices, and Ktorfit sample.
</instructions>

<version_matrix>

## Version Compatibility Matrix (2026)

| Kotlin | KSP Version | Gradle | AGP | Java |
|---|---|---|---|---|
| `2.4.0` | `2.3.9` (KSP2 default) | `7.6.3` - `9.5.0` | `8.5.2` - `9.1.0` | `17`+ |
| `2.3.20` | `2.3.7` | `7.6.3` - `9.5.0` | `8.5.2` - `9.1.0` | `17`+ |
| `2.0.x` | `2.0.0` - `2.0.21` | `7.4` - `8.10` | `8.0` - `8.5` | `17`+ |

</version_matrix>

<reference_index>

## Reference Index

- [ksp1-vs-ksp2.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/ksp1-vs-ksp2.md)
  - Detailed differences: DFS overrides, container error type resolution, star projections, Enum entry types, volatile modifier, varargs, synthesized members, super types, and Gradle daemon heap sizing.
  - *Read when*: Transitioning KSP1 code to KSP2 or resolving behavior discrepancies.
- [syntax-and-classes.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/syntax-and-classes.md)
  - Processing API and AST symbols. Methods on `SymbolProcessor`, `Resolver`, `CodeGenerator`, `Dependencies`, and `KS*` classes.
  - *Read when*: Writing KSP processor code or mapping AST structures.
- [configuration.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/configuration.md)
  - Gradle plugin configs, KMP target-specific configurations, `gradle.properties` tuning, CLI options, and daemon debugging.
  - *Read when*: Setting up builds, target configurations, or debugging build runs.
- [best-practices.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/best-practices.md)
  - Performance rules: avoid eager resolve, precise dependency mapping, deterministic sorting, caching restrictions, and KSP2 default value parsing.
  - *Read when*: Optimizing compilation speed, fixing build cache issues, or resolving PSI-lifetime errors.
- [sample-ktorfit.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/sample-ktorfit.md)
  - Ktorfit-style processor implementation sample showing SymbolProcessorProvider, SymbolProcessor, and CodeGenerator with isolating dependencies.
  - *Read when*: Reviewing clean, real-world KSP implementation templates.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "ClassCastException or PSI-lifetime error under KSP2" | [best-practices.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/best-practices.md) |
| "Migrate Room or Hilt build config to KSP2" | [configuration.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/configuration.md) |
| "How KSP2 override order differs from KSP1 BFS" | [ksp1-vs-ksp2.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/ksp1-vs-ksp2.md) |
| "Isolating vs Aggregating output generation syntax" | [syntax-and-classes.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/syntax-and-classes.md) |
| "How to configure KSP for multiplatform (KMP) sourceSets" | [configuration.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/configuration.md) |
| "Why KSP2 does not resolve default value in annotations" | [best-practices.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/best-practices.md) |
| "Resolve Map<String, NonExistentType> behavior difference" | [ksp1-vs-ksp2.md](file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/ksp1-vs-ksp2.md) |

</routing_table>

<constraints>
- Developers **must** verify Kotlin/KSP versions against compatibility matrix first.
- Use **only** target-specific dependencies for KMP (`kspJvm`, `kspCommonMainMetadata`).
- You **must** never cache `KS*` symbol objects between rounds. Use plain data classes.
- You **should** explicitly declare isolating dependencies (`aggregating = false`) unless aggregating indexes.
- Refer to reference files using absolute file paths under `file:///Users/jsanjaya/.gemini/config/skills/ksp-expert/references/`.
- When asked about compilation, incrementality, or configs, you **must** structure your response format cleanly and specify the exact file path link to the relevant reference document.
</constraints>
