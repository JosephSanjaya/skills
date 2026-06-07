---
name: prompt-framework
description: High-signal prompt structure, XML tags, triage protocol, and effort level selection for Claude Code prompts
metadata:
  type: reference
---

# High-Signal Prompt Framework

## Five-Pillar Template

```
Goal: [one sentence — what done looks like]
Context: @file:line or raw error/log output
Constraints: [hard limits — no mocks, ES modules only, etc.]
Verify: [exact command that proves success]
Next: [first step only]
```

## Bug Triage Protocol

| Pillar | Content | Why |
|--------|---------|-----|
| Summary | Feature + failure in one sentence | Anchors focus, prevents broad scan |
| Observed | Exact error, stack trace, timestamp | Direct pattern match, no interpretation |
| Expected | Intended outcome per spec | Defines success boundary |
| Repro | Minimal steps to trigger | Isolates logical failure path |
| Environment | Version, branch, config flags | Eliminates execution context guesswork |

**Rule:** Paste raw CI output / stack trace directly. Don't narrate it.  
Raw trace → agent traces root cause directly. Narrative → agent spends tokens re-interpreting.

---

## XML Tag Semantic Isolation

Claude trained to treat XML tags as semantic separators. Prevents context bleed.

```xml
<task>
  <goal>Fix JWT expiry check in auth middleware</goal>
  <context>
    @src/auth/middleware.ts:45
    Error: TokenExpiredError at line 45
    Stack: ...
  </context>
  <constraints>
    - No new dependencies
    - Must pass existing test suite
  </constraints>
  <verify>npm test -- auth.test.ts</verify>
</task>
```

**Nesting tags > flat lists** for predictability.  
`<thinking>` before code → 30-40% accuracy improvement on complex changes.

---

## Effort Level Selection

| Level | Use When | Avoid When |
|-------|----------|------------|
| Low | Typos, renames, linter fixes, boilerplate | Any multi-file reasoning |
| Medium | Feature add, standard bug fix | Unclear root cause |
| High | Multi-file refactor, unclear causality | Simple one-liner fix |
| Max | Race conditions, memory leaks, core design | Anything else (costs 10x) |

**Iterative escalation rule:** Start Low → step up only if result unsatisfactory.  
**Critical:** High/Max effort can't compensate for missing context. Fix context first, then escalate.

---

## Context-Bounding Operators

| Operator | Effect |
|----------|--------|
| `@file` | Read specific file into context |
| `@file:line` | Read file at line — most precise |
| `!command` | Run command output directly into context |
| `#symbol` | Reference symbol without full file read |

Examples:
```
@src/auth/middleware.ts:45
!git log --oneline -5
!npm test -- --testPathPattern=auth 2>&1 | tail -20
```

---

## Structural Optimization Mechanisms

### Global State Management with CLAUDE.md
Eliminate repetition of project-specific rules (naming conventions, architecture patterns, stack constraints) by using a hierarchical lookup:
1. **Global**: `~/.claude/CLAUDE.md` - Cross-project settings
2. **Project**: `<project-root>/CLAUDE.md` - Project-specific rules
3. **Subdirectory**: `<subdirectory>/CLAUDE.md` - Module-specific rules (for monorepos)
Saves 2,000+ tokens per session by avoiding repeated instructions.

### Model Context Protocol (MCP) Dynamic Loading
Instead of pushing entire documentation sets or database schemas into prompts, configure MCP servers to dynamically query specific packages or databases only when needed.
Example MCP Configuration (`mcp_config.json`):
```json
{
  "mcpServers": {
    "docs": {
      "command": "uvx",
      "args": ["mcp-server-docs@latest"]
    }
  }
}
```

### Deterministic Aliasing with /commands
Replace verbose natural language instructions with structured command definitions.
Example Command Definition:
```yaml
/test-and-fix:
  description: Run Vitest, identify errors, apply fixes
  steps:
    - Run: npm run test
    - Parse: Extract failing tests
    - Fix: Apply corrections
    - Verify: Re-run tests
```
Saves ~300 tokens of intent per request by replacing it with a ~10-token command alias.

---

## Anti-Patterns

| Anti-pattern | Cost | Fix |
|-------------|------|-----|
| "Fix the bug in auth module" | 40k+ tokens exploration | Provide file:line + stack trace |
| Narrating error in prose | Ambiguity overhead | Paste raw output |
| Asking for "entire feature" | Context overflow | First step only, then next |
| Max effort on obvious fix | 10x token cost | Low effort first |
| Multiple tasks in one prompt | Context bleed | One task per session unit |
