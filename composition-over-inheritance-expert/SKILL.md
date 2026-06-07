---
name: composition-over-inheritance-expert
description: "Kotlin Composition Over Inheritance expert. Use when: designing composable architectures with 'by' delegation, refactoring inheritance hierarchies to composition, debugging delegation bugs (loss of self, mutable delegate trap, Java default method bypass, equals/hashCode gap), configuring Spring/JPA/Hibernate for Kotlin, Android ViewModel delegation, lazy delegate thread-safety, value class zero-cost wrappers. Triggers on: composition over inheritance, class delegation, by keyword, delegate bug, refactor inheritance, fragile base class, interface segregation, delegating to interface, ViewModel delegate, sealed class vs composition, lazy delegate Android, open class, kotlin-allopen, kotlin-jpa plugin, JPA data class, value class wrapper."
---

# Composition Over Inheritance Expert

<instructions>
Provide expert guidance on Kotlin Composition Over Inheritance (COI) patterns, interface delegation, value classes, compiler plugins, and framework configurations. Check the reference files below for detailed guidelines, bytecode analysis, and refactoring recipes.
</instructions>

<decision_matrices>

## Inheritance vs Composition Decision Matrix

| Criterion | Composition (Preferred) | Inheritance |
|---|---|---|
| **Relationship** | Has-A / Uses-A | Is-A |
| **Lifecycle** | Independent, dynamic, swappable | Bound to parent class |
| **Taxonomy** | Orthogonal behavior dimensions | Strict, immutable hierarchy |
| **Examples** | `strategy`, `renderer`, `listener` | Sealed class state (`UiState`), compiler-enforced types |
| **Testing** | Easy to mock, stub, or swap | Hard to isolate from parent |

**Golden Rule:** If "B IS-A A" does not hold true in all contexts forever → use composition.

</decision_matrices>

<production_bugs>

## Top 5 Delegation and Composition Pitfalls

1. **Loss of Self (this Escape)**: Delegate has no knowledge of wrapper; self-use calls in delegate bypass wrapper overrides.
   - *Fix*: Explicitly override coordinating methods in the delegator. (See [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md))
2. **Mutable Constructor Delegate Trap**: Reassigning a `var` constructor-injected delegate does not update compiled final `$$delegate_0`.
   - *Fix*: Implement manual method forwarding instead of relying on `by` delegation. (See [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md))
3. **Java Default Method Bypass**: Kotlin `by` delegation does not generate overrides for Java default methods, bypassing delegate overrides.
   - *Fix*: Manually override and forward methods in the delegator. (See [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md))
4. **Any Methods Gap (equals/hashCode)**: `by` delegation does not forward `equals()`, `hashCode()`, or `toString()`, using JVM Object defaults instead.
   - *Fix*: Declare them in the interface or manually override them. (See [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md))
5. **data class for JPA Entities**: Kotlin `data class` forces eager initialization of lazy fields (triggering N+1 queries) and breaks CGLIB proxying.
   - *Fix*: Use standard `open class` for JPA entities, and implement `equals()`/`hashCode()` manually. (See [enterprise.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/enterprise.md))

</production_bugs>

<reference_index>

## Reference Index

- [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md)
  - Detailed explanations and code examples for Loss of self, mutable constructor delegate trap, Java default method bypass, Any methods gap, and interface-only constraints.
  - *Read when*: Debugging delegation bugs, incorrect forwarding, or runtime behavior anomalies.
- [patterns.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/patterns.md)
  - Class delegation bytecode analysis, encapsulated constructor pattern, interface segregation (ISP) + multi-delegation, refactoring recipes (Inheritance → Composition), Android ViewModel delegation, value classes, and lazy thread-safety modes.
  - *Read when*: Designing composed systems, performance optimizing lazy states, or using zero-cost value class wrappers.
- [enterprise.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/enterprise.md)
  - Spring Boot CGLIB proxying fixes (`kotlin-spring`/`kotlin-allopen` plugins), JPA/Hibernate configurations, Gradle/Maven compiler setups (including Kotlin 2.3.20+ automatic `all-open` for `kotlin.plugin.jpa`), Android lifecycle-aware delegates, and sealed class legitimate inheritance.
  - *Read when*: Configuring Kotlin Spring/JPA enterprise applications, or implementing Android lifecycle delegates.

</reference_index>

<routing_table>

## Guide Routing

| Symptom / Query | Reference |
|---|---|
| "override in delegator ignored by delegate" or "this escape" | [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md) |
| "changing var delegate has no effect" or "mutable delegate" | [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md) |
| "Java default method not called through delegate" | [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md) |
| "equals/hashCode using reference equality instead of delegate" | [pitfalls.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/pitfalls.md) |
| "how does Kotlin by delegate decompile under the hood" | [patterns.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/patterns.md) |
| "how to refactor deep inheritance hierarchy to composition" | [patterns.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/patterns.md) |
| "Android ViewModel delegation without base class inheritance" | [patterns.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/patterns.md) |
| "lazy thread safety mode optimization for UI thread" | [patterns.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/patterns.md) |
| "lazy-loading entities trigger N+1 queries" or "Spring proxy failure" | [enterprise.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/enterprise.md) |
| "JPA entities data class vs open class" | [enterprise.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/enterprise.md) |
| "Kotlin 2.3.20+ JPA all-open compiler plugin automatic preset configuration" | [enterprise.md](file:///Users/jsanjaya/.gemini/config/skills/composition-over-inheritance-expert/references/enterprise.md) |

</routing_table>

<constraints>
- Interface delegation target MUST be an interface (Kotlin constraint).
- Never use Kotlin `data class` for JPA/Hibernate entity classes.
- Ensure Spring/JPA classes and properties are `open` (using `kotlin-spring`/`kotlin-allopen` or Kotlin 2.3.20+ `kotlin.plugin.jpa` with auto-allopen preset) for lazy loading and CGLIB proxying.
- Explicitly override `equals()`, `hashCode()`, and `toString()` on delegators to avoid reference-equality issues.
- All code examples must adhere to safe coroutine scoping and lifecycle boundaries in concurrent/Android environments.
- All reference files and linked documentation must be referenced using their absolute file:/// paths, and should be linked correctly.
</constraints>
