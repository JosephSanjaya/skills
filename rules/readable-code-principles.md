---
title: Readable Code Principles
description: Core principles for writing self-documenting, readable code with strict comment guidelines - comments explain why, not what
inclusion: auto
---

# Readable Code Principles

<rules>
- **Intent-Revealing Names:** use clear intent; no abbreviations unless universally understood
- **Variables:** nouns (e.g., `userCount`, `activeSessions`)
- **Functions:** verbs (e.g., `fetchUser`, `validateEmail`); limit to <20 lines; enforce single responsibility
- **Booleans:** predicates (e.g., `isValid`, `hasPermission`, `canEdit`)
- **Flat Structure:** avoid deep nesting; use early returns and guard clauses
- **Complex Conditions:** extract into named variables or functions

## Comments: why only, never what

- **Allowed:** non-obvious business logic, workarounds for external bugs, non-obvious consequences, complex algorithms that cannot be simplified.
- **Prohibited:** explaining obvious code, restating code in English, commented-out code.
- **Pre-requisite:** rename, extract, or simplify code to avoid comments where possible.
</rules>

<constraints>
All comments and code must follow these constraints. You should write self-documenting code only.
</constraints>
