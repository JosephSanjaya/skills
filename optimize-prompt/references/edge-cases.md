---
name: edge-cases
description: Edge cases, failure modes, and recovery patterns for Claude Code prompt optimization
metadata:
  type: reference
---

# Edge Cases and Failure Modes

## Context Decay Symptoms

| Symptom | Cause | Fix |
|---------|-------|-----|
| Agent ignores coding standards | Window >70% full | `/compact` then re-state constraints |
| Repeating previously corrected mistakes | Foundational instructions deprioritized | `/clear` + include constraints in new prompt |
| Over-engineered solutions | Context drift after many turns | `/rewind` to last good state |
| Slow responses | Near-saturation attention overhead | Set compactionThreshold to 0.85 |

## Compaction Lossy Failure

**Problem:** `/compact` summarizes history but drops edge cases, subtle constraints, and implementation decisions.

**Detection:** After compaction, ask "what are the current constraints?" — if agent can't enumerate them correctly, compaction lost critical state.

**Prevention:** 
1. Use PreCompact hook to snapshot to file
2. Keep implementation decisions in CLAUDE.md, not conversation
3. After compaction, re-state key constraints explicitly

## Effort Level Misfires

**Max effort + missing context:**  
Agent spends thousands of tokens reasoning about incomplete information. Output is still wrong.  
Fix: provide context FIRST, then escalate effort if needed.

**Low effort + complex multi-file change:**  
Pattern-matching produces plausible but incorrect result — will pass syntax checks but fail semantics.  
Fix: recognize when root cause spans >2 files → escalate to Medium minimum.

**Symptoms of wrong effort level:**
- Low on complex: code looks right, logic is wrong
- High/Max on simple: excessive reasoning preamble, same output as Low would give

## XML Tag Edge Cases

**Nested `<context>` with user-supplied data:**  
If pasting external content (API responses, logs) inside XML tags, wrap in CDATA or use different tag name to avoid parser confusion.

```xml
<task>
  <goal>Debug auth failure</goal>
  <raw_log><![CDATA[
    ERROR 2026-05-15: TokenExpiredError: jwt expired
    at /app/auth.js:45:3
  ]]></raw_log>
</task>
```

**`<thinking>` tag misuse:**  
Don't ask Claude to put final code inside `<thinking>`. Thinking is pre-reasoning, not output.  
Correct: `<thinking>` → then code block outside tags.

## Subagent Failure Patterns

**Open-ended subagent prompt:**  
"Research the auth module" → subagent reads entire codebase → returns 10k token summary → defeats purpose.  
Fix: specify exact output format and scope.

**Subagent with wrong tool permissions:**  
Reviewer subagent with Write permission → accidentally modifies code during audit.  
Fix: always restrict Reviewer to Read+Grep+Glob only.

**Parent-subagent context sync:**  
Subagent has no session history. If it needs context from parent session, include it explicitly in the subagent prompt — don't reference "what we discussed."

## CLAUDE.md Bloat Failure

**File >200 lines:**  
Every prompt consumes proportionally more input tokens. At 400 lines, overhead may exceed benefit.

**Diagnostic:**
```bash
wc -l .claude/CLAUDE.md  # should be <200
```

**Fix:** Move detailed examples to references/. Keep CLAUDE.md as entry point with @-links.

**Including standard conventions:**  
"Use camelCase for variables" wastes tokens on what Claude already knows. Only include non-obvious project-specific rules.

## MCP + CLI Conflict

Running MCP server alongside CLI tools for same service (e.g., GitHub MCP + `gh` CLI):  
Agent may default to MCP (higher token cost, lower reliability) when both available.

**Fix:** In CLAUDE.md explicitly state: "Prefer `gh` CLI over GitHub MCP for all repository operations."

## Multi-Session Sync Failures

**Handoff doc stale:**  
Session B acts on outdated API contract from Session A's handoff doc.  
Fix: include timestamp and git SHA in handoff docs.

```markdown
# API Handoff
Generated: 2026-05-15T14:30Z | SHA: abc1234
```

**Parallel session conflicts:**  
Two sessions editing same file → merge conflict.  
Fix: assign non-overlapping file ownership per session. Never let two sessions own same file.
