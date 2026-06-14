---
name: compose-component-expert
description: "Expert guide for designing, building, and optimizing reusable Jetpack Compose components. Applies 2026 best practices, Style API, slot APIs, Modifier.Node, strong skipping mode, recomposition optimization, and Detekt/Ktlint rules validation. Trigger this skill whenever the user asks about Jetpack Compose component design, custom modifiers, skippability, derivedStateOf, modifier parameter order, custom layouts, or needs help with Compose-specific performance bottlenecks."
---

# Compose Component Expert

Design + optimize reusable Jetpack Compose components. 2026 standards.

<instructions>
Use smart caveman mode prose. Maintain token efficiency. Code snippets must be type-safe.
Refer to specific markdown files in references/ for deep details.
</instructions>

## 1. Quick Decision Matrix

| Target | Tool / Standard | Details |
| :--- | :--- | :--- |
| **API Design** | Slot APIs, stateless/stateful splits | [best-practices.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/best-practices.md) |
| **Performance** | Strong skipping, derivedStateOf, stability | [performance.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/performance.md) |
| **New APIs** | Modifier.Node, Style API, SharedElement | [new-apis-2026.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/new-apis-2026.md) |
| **Static Rules** | Detekt / Ktlint compose rules | [detekt-rules.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/detekt-rules.md) |

## 2. Directory Structure

<references>
- **References**:
  - [best-practices.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/best-practices.md) — API design rules, param ordering, naming.
  - [performance.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/performance.md) — Stability, recomposition scopes, derivedStateOf, AOT profiles.
  - [new-apis-2026.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/new-apis-2026.md) — Modifier.Node, Style API, Predictive Back.
  - [detekt-rules.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/detekt-rules.md) — Detekt/Ktlint rules index.
</references>

<samples>
- **Samples**:
  - [SlotApiComponent.kt](file:///Users/jsanjaya/Projects/skills/compose-component-expert/samples/SlotApiComponent.kt) — Slot pattern + scope constraints.
  - [ModifierNodeComponent.kt](file:///Users/jsanjaya/Projects/skills/compose-component-expert/samples/ModifierNodeComponent.kt) — Modifier.Node element + state update.
  - [StyleApiComponent.kt](file:///Users/jsanjaya/Projects/skills/compose-component-expert/samples/StyleApiComponent.kt) — Style API presses & transitions.
</samples>

## 3. Related Compose Skills

Jump to specialized skills:
- [adaptive](file:///Users/jsanjaya/.gemini/config/skills/android-jetpack-compose-adaptive/SKILL.md) — Adaptive/multi-pane UI layouts.
- [edge-to-edge](file:///Users/jsanjaya/.gemini/config/skills/android-system-edge-to-edge/SKILL.md) — System bar margins, IME insets.
- [jetpack-compose-m3-theme-expert](file:///Users/jsanjaya/.gemini/config/skills/jetpack-compose-m3-theme-expert/SKILL.md) — Material 3 custom theming.
- [migrate-xml-views-to-jetpack-compose](file:///Users/jsanjaya/.gemini/config/skills/android-jetpack-compose-migration-migrate-xml-views-to-jetpack-compose/SKILL.md) — Legacy XML migration.
- [navigation-3](file:///Users/jsanjaya/.gemini/config/skills/android-navigation-navigation-3/SKILL.md) — Navigation 3 Scenes & backstacks.
- [styles](file:///Users/jsanjaya/.gemini/config/skills/android-jetpack-compose-theming-styles/SKILL.md) — Component styles API integration.

<constraints>
- Expose stateless Slot APIs; trailing lambda last; first optional param MUST be `modifier: Modifier = Modifier`.
- Use primitive State holders (`mutableIntStateOf`) to avoid autoboxing.
- Use `Modifier.Node` instead of `composed {}`.
- Style API transitions must run in layout/draw phases using `pressed(Style { animate(Style { ... }) })` structures.
- Code should be clean, type-safe, and conform to the schema required in [detekt-rules.md](file:///Users/jsanjaya/Projects/skills/compose-component-expert/references/detekt-rules.md) to pass CI audits.
</constraints>
