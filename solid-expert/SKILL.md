---
name: solid-expert
description: "Kotlin & Compose Multiplatform SOLID Expert. Applies SOLID principles with a strong preference for composition over inheritance (COI) to build professional, clean, maintainable, and testable mobile/multiplatform applications. Use when: designing architectures, refactoring deep class hierarchies, debugging class delegation, configuring Spring/JPA all-open compiler plugins, managing Android ViewModel/Fragment delegates, preventing memory leaks, and writing value classes or sealed interfaces."
---

# SOLID & Composition Over Inheritance Expert

<instructions>
Provide senior Kotlin and Android engineering guidance on applying SOLID principles, Clean Architecture, and Compose Multiplatform patterns. Always prioritize composition over inheritance unless representing finite, closed state taxonomies. Address class delegation bugs, JPA compiler plugins, value classes, and lifecycle-aware delegate leaks. Use the references below for deep dives.
</instructions>

<decision_matrices>

## Inheritance vs Composition Decision Matrix

| Criterion | Composition (Preferred) | Inheritance |
|-----------|-------------------------|-------------|
| **Relationship** | Has-A / Uses-A | Is-A |
| **Lifecycle** | Independent, dynamic, swappable | Bound tightly to parent class |
| **Taxonomy** | Orthogonal behavior dimensions | Strict, immutable hierarchy |
| **Use Case** | Strategy, renderer, database, repository | Sealed interface state (`UiState`) |
| **Testing** | Easy to mock, stub, or swap in isolation | Hard to isolate from parent behavior |

**Golden Rule:** If "B IS-A A" does not hold true in all contexts forever, use composition.

</decision_matrices>

<production_bugs>

## Critical Delegation and Architecture Pitfalls

1. **Loss of Self (this Escape)**: Delegate has no knowledge of wrapper; self-use calls in delegate bypass wrapper overrides.
   - *Fix*: Explicitly override coordinating methods in the delegator. (See [coi-patterns-and-pitfalls.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/coi-patterns-and-pitfalls.md))
2. **Mutable Constructor Delegate Trap**: Reassigning a `var` constructor-injected delegate does not update compiled final `$$delegate_0`.
   - *Fix*: Implement manual method forwarding instead of relying on `by` delegation. (See [coi-patterns-and-pitfalls.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/coi-patterns-and-pitfalls.md))
3. **Java Default Method Bypass**: Kotlin `by` delegation does not generate overrides for Java default methods, bypassing delegate overrides.
   - *Fix*: Manually override and forward Java default methods. (See [coi-patterns-and-pitfalls.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/coi-patterns-and-pitfalls.md))
4. **Any Methods Gap (equals/hashCode)**: `by` delegation does not forward `equals()`, `hashCode()`, or `toString()`, using JVM Object defaults instead.
   - *Fix*: Manually override them on the delegator. (See [coi-patterns-and-pitfalls.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/coi-patterns-and-pitfalls.md))
5. **data class for JPA Entities**: Kotlin `data class` forces eager initialization of lazy fields, breaking CGLIB proxying and triggering N+1 queries.
   - *Fix*: Use `open class` for JPA entities, and implement `equals()`/`hashCode()` manually. (See [enterprise-and-platform.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/enterprise-and-platform.md))

</production_bugs>

<reference_index>

## Reference Index

- [solid-principles.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/solid-principles.md)
  - Detailed guide on SRP, OCP, LSP, ISP, and DIP. Kotlin and Compose patterns showing how to fulfill each principle via composition.
- [coi-patterns-and-pitfalls.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/coi-patterns-and-pitfalls.md)
  - Kotlin class delegation (`by`) bytecode analysis, encapsulated constructor pattern, multi-delegation, refactoring recipes, zero-cost value classes, and lazy thread-safety modes.
- [enterprise-and-platform.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/enterprise-and-platform.md)
  - Spring Boot CGLIB proxying, `kotlin-spring`/`kotlin-allopen` plugins, JPA/Hibernate entity design, Android ViewModel composition, Fragment lifecycle delegates, and legitimate inheritance (sealed classes).
- [clean-code-and-testing.md](file:///Users/jsanjaya/Projects/skills/solid-expert/references/clean-code-and-testing.md)
  - Clean Kotlin coding rules (early returns, guards, sizes), object stereotypes, testing stack (MockK, Turbine, JUnit, Compose UI), TDD lifecycle, and code smell detection.

</reference_index>

<constraints>
- Interface delegation target MUST be an interface (Kotlin compiler requirement).
- Never use Kotlin `data class` for JPA/Hibernate entities.
- Ensure Spring/JPA classes and properties are `open` (using `kotlin-spring`/`kotlin-allopen` or Kotlin 2.3.0+ presets) for lazy loading and CGLIB proxying.
- Explicitly override `equals()`, `hashCode()`, and `toString()` on delegators to avoid reference-equality issues.
- All code examples must adhere to safe coroutine scoping and lifecycle boundaries in concurrent/Android environments.
- Reference files and linked documentation must be referenced using only their absolute file:/// paths.
</constraints>
