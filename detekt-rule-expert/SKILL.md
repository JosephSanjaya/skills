---


name: detekt-rule-expert
description: Expert guide for custom Detekt rules (1.x/2.0) & Jetpack Compose quality checks. Use when creating custom Detekt rules, writing AST/PSI visitors, configuring detekt.yml, managing Kotlin type resolution (Analysis API), or enforcing Compose performance/state hoisting.
---

# Detekt Rule Expert

<instructions>
Direct user to write compile-safe, high-performance Detekt rules. Target AST/PSI verification patterns for standard Kotlin and Jetpack Compose constructs. Use pointers. Keep text dense. No filler.
</instructions>

<rules>
## 1. Custom Rules Foundation

- **AST Callback**: Override narrowest node visitor. Do not walk tree if precondition fails.
- **Detekt 1.x vs 2.0**: FQNs, base class constructor, report types, ServiceLoader paths differ.
  - *Reference*: [rules.md](file:///Users/jsanjaya/Projects/skills/detekt-rule-expert/references/rules.md)
- **Type Resolution**: 1.x uses `BindingContext`; 2.0 uses K2 Analysis API `analyze(element) {}`.
  - *Reference*: [types.md](file:///Users/jsanjaya/Projects/skills/detekt-rule-expert/references/types.md)
- **Auto-Correction**: Wrap mutations in `withAutoCorrect {}`. Build AST using `KtPsiFactory`. Swap with `astReplace`.
  - *Reference*: [autocorrect.md](file:///Users/jsanjaya/Projects/skills/detekt-rule-expert/references/autocorrect.md)

---

## 2. Jetpack Compose AST Rule Parsing

Guidelines for implementing rules that analyze Jetpack Compose specific AST/PSI patterns.
- *Reference*: [compose.md](file:///Users/jsanjaya/Projects/skills/detekt-rule-expert/references/compose.md)

### Key Parsing Strategies
1. **Composable Detection**: Check `@Composable` annotations on functions and getters. Filter out overrides, interface functions, and `@Preview` methods.
2. **Layout Emitters Count**: Recursively traverse statements in loops/conditionals to count layout-emitting functions (allowlist-based checking).
3. **Modifier Tracing**: Track modifier reassignments and chain manipulations (`val modifier2 = modifier.fillMaxWidth()`) inside block statements. Verify that modifier parameter is applied to the root node and not reused in descendants.
4. **ViewModel Forwarding Check**: Match parameter types with regex (`.*ViewModel|.*Presenter`) and scan for nested UI call expressions forwarding these references as arguments.
5. **CompositionLocal & Remember**: Identify `staticCompositionLocalOf` property declarations and verify if calls (e.g. `movableContentOf`) are wrapped in `remember` parent call scopes.

---

## 3. Configuration & Suppression

- **detekt.yml**: Define rulesets, enable/disable, set severity (`error` | `warning` | `info`).
- **Validation Excludes**: Exclude custom properties in `config.excludes` to prevent validation crashes.
- **Code Excludes**: Filter out `/build/generated/` at Gradle-task level.
- **Suppression**: Use `@Suppress("RuleId")` or `@file:Suppress(...)`.
- *Reference*: [config.md](file:///Users/jsanjaya/Projects/skills/detekt-rule-expert/references/config.md)

---

## 4. Verification Script

Verify custom rules module structure, `compileOnly` scopes, ServiceLoader registration, and `detekt.yml` setup.
- *Script*: [check_detekt_setup.py](file:///Users/jsanjaya/Projects/skills/detekt-rule-expert/scripts/check_detekt_setup.py)
- *Usage*: `python3 scripts/check_detekt_setup.py <path_to_rules_project_root> [path_to_detekt_yml]`

</rules>

<constraints>
- Custom rules **must** declare `detekt-api` as `compileOnly`.
- If custom rule set uses config keys, you **must** exclude them under `config.excludes` in `detekt.yml`.
- Never use `compositionLocalOf` for stable theme tokens; **should** only use `staticCompositionLocalOf`.
</constraints>
