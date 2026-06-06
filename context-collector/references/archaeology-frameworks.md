# Software Archaeology Frameworks

## Rozlog/OOPSLA — 6 Steps

| Step | Action | Output |
|------|--------|--------|
| 1 | Inheritance assessment | Structural footprint, ownership boundaries |
| 2 | Static syntax analysis | Class signatures, interfaces, language primitives |
| 3 | Call-flow tracing | Preliminary dependency graph |
| 4 | Dysfunctional process ID | Unused/obfuscated/poorly designed modules |
| 5 | Scary section isolation | Volatile, unmaintained, high-complexity modules |
| 6 | Targeted refactoring | Stabilize before extending |

## Feathers' Quick Onboarding — 6 Steps

| Step | Action | Why |
|------|--------|-----|
| 1 | Open IDE, browse dir layout + import chains | Desensitizes codebase size fear |
| 2 | Find DTOs, Value Objects, core schemas only | Bypass execution dread |
| 3 | Ask Dev/Design/Product/QA about runtime bugs | Get tribal knowledge |
| 4 | `git log` last 3 months | Find pattern drift + team misconceptions |
| 5 | Get deterministic local build running | Prove env + dependency alignment |
| 6 | Small mutation: unit test + variable rename | Confirm dynamic behavior |

## Edge-Diving Tactic

1. Pick specific user-visible use-case
2. Find unique static UI string (e.g. "Select Departure") or CSS class
3. If string too common → switch app locale to secondary language (Dutch, etc.) for unique strings
4. Set debugger breakpoints at that string's handler
5. Execute use-case → pause → read call stack
6. Trace backward from call stack (bottom-up)
7. Alternate with top-down: stop tracing, inspect data layout (who owns state, object lifecycles)
8. Small safe refactors (rename vars, add comment) to solidify understanding
9. Externalize mental model to paper/doc — prevent cognitive overload

## Comprehension Model Summary

| Model | Strategy | Use When |
|-------|----------|----------|
| Pennington | Bottom-up, statement-by-statement, CFG → situation model | Zero domain familiarity |
| Soloway et al. | Top-down, match programming plans to code | Prior domain knowledge |
| Letovsky | Opportunistic: switch based on "beacons" (named functions like `verifyCredentials`) | Mixed familiarity |
| Von Mayrhauser | Simultaneous domain + program + situation models | Complete comprehension target |

**Beacons** = obvious indicators (function named `processPayment`, class named `AuthMiddleware`) — use these as entry points.
