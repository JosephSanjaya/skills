---
title: Code Structure Patterns
description: Patterns for organizing code structure, functions, variables, and data to maximize readability and maintainability
inclusion: auto
---

# Code Structure Patterns

<rules>
- **Functions:** narrative flow (high → low level); early returns first; extract complex blocks
- **Variables:** declare close to first use; minimize lifetime
- **Grouping:** blank lines between logical steps; related ops stay together
- **Naming (Kotlin):**
  - Functions/vars: `camelCase`
  - Classes: `PascalCase`
  - Constants: `SCREAMING_SNAKE_CASE`
  - Packages: `lowercase`
  - Specify intent clearly (e.g., `userCount` instead of `count`)
- **Error handling:** throw, don't return null silently; fail fast with `require`/`check`
- **Data structures:** Set for uniqueness, Map for lookup, List for ordered; prefer data classes over Pair/Triple
</rules>

<constraints>
All code changes must conform to these structure rules. You should write clean and compliant code only.
</constraints>
