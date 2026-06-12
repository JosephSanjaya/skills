---
name: detekt-rule-expert
description: Expert guide for custom Detekt rules (1.x/2.0) & Jetpack Compose quality checks. Use when creating custom Detekt rules, writing AST/PSI visitors, configuring detekt.yml, managing Kotlin type resolution (Analysis API), or enforcing Compose performance/state hoisting.
---

# Detekt Rule Expert

<instructions>
Direct user to write compile-safe, high-performance Detekt rules. Target AST/PSI verification patterns for standard Kotlin and Jetpack Compose constructs. Check the reference index and routing table below to target specific details.
</instructions>

<rules>

## 1. Reference Index

- [rules.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/rules.md): Base classes, AST callbacks, ServiceLoader registration, and Detekt 1.x vs 2.0 differences. Read when writing basic custom rules.
- [types.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/types.md): Resolving Kotlin type definitions using K1 `bindingContext` vs K2 Analysis API `analyze(element) {}`. Read when rules require type/symbol resolution.
- [autocorrect.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/autocorrect.md): Auto-correction, AST mutations with `KtPsiFactory`/`astReplace`, and resolving headless compiler test environment crashes. Read when writing autocorrect rules.
- [baseline.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/baseline.md): Generating stable signatures, anchoring findings to named parent declarations, and preventing baseline bypasses. Read when rules ignore baselines.
- [compose.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/compose.md): Jetpack Compose AST/PSI checks, modifier reuse, viewmodel forwarding, and remember/composition local validation. Read for Compose-specific checks.
- [config.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/config.md): Detekt configuration (`detekt.yml`), setting severities, rule suppression, excluding custom config properties, and registering custom scoped Detekt Gradle tasks (autoCorrect on git diff / branch commits). Read for config, suppression, and custom task patterns.

---

## 2. Guide Routing

| Symptom / Query | Reference |
|---|---|
| "Write custom rule or register ServiceLoader" | [rules.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/rules.md) |
| "Resolve types or use K2 compiler analyze {}" | [types.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/types.md) |
| "Implement auto-correction or fix headless unit test failures" | [autocorrect.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/autocorrect.md) |
| "Rule bypasses baseline or generates unstable signature" | [baseline.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/baseline.md) |
| "Compose AST check (ViewModel forwarding, Modifier reuse)" | [compose.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/compose.md) |
| "Configure detekt.yml, suppress rules, or set severity" | [config.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/config.md) |
| "Register custom scoped Detekt task (autoCorrect on git diff or branch commits)" | [config.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/config.md) §6 |
| "Config cache error with custom Detekt task on Gradle 9+" | [config.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/config.md) §6 |
| "source() / setSource() ignored inside doFirst" | [config.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/config.md) §6 |
| "Verify custom rules project structure and dependency scopes" | See Automation Scripts below |

---

## 3. Automation Scripts

```bash
# Verify custom rule project structure and detekt.yml configuration:
python3 /Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/scripts/check_detekt_setup.py <path_to_rules_project_root> [path_to_detekt_yml]
```

</rules>

<constraints>
- All reference files and linked documentation **must** be referenced using their absolute file:/// paths under `/Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/`.
- Custom rules **must** declare `detekt-api` as `compileOnly` dependency scope.
- If custom rule set uses config keys, you **must** exclude them under `config.excludes` in `detekt.yml`.
- Never use `compositionLocalOf` for stable theme tokens; **should** only use `staticCompositionLocalOf`.
</constraints>
