---
name: subagents-and-scaling
description: Subagent patterns, horizontal scaling, MCP vs CLI token economics, and multi-session handoff
metadata:
  type: reference
---

# Subagents and Scaling

## When to Use Subagents

Delegate to subagent when main session would be flooded with noise:
- Searching massive logs
- Deep research on new library/API
- Scanning large directory for dependencies
- Security/quality audit post-implementation

Subagent operates in own 200k window → returns concise summary → main context stays clean.

## Subagent Configuration

| Type | Task | Model | Tool Permissions |
|------|------|-------|-----------------|
| Explorer | Codebase search, dependency mapping | Haiku 4.5 | Read, Grep, Glob |
| Researcher | External docs, API analysis | Haiku or Sonnet | Read, WebFetch |
| Reviewer | Bug/security audit | Sonnet or Opus | Read, Grep, Glob (no Write!) |
| Planner | Multi-step strategy | Sonnet 4.6 | Read, Grep |

Hard-restrict Reviewer to read-only tools. Prevents accidental modification. Also simplifies parent reasoning.

## Claude Code Agent Tool Usage

```
Agent({
  subagent_type: "Explore",
  prompt: "Find all usages of deprecated TokenV1 class. Return file:line list only, no suggestions.",
  description: "Locate deprecated token usages"
})
```

**Prompt rules for subagents:**
- State exact output format ("return file:line list only")
- Give all context upfront — subagent has no session history
- Bound the task precisely — open-ended = expensive

## Horizontal Scaling

Full-stack project → separate sessions per module:
- Session A: Backend (Go/pkg/)
- Session B: Frontend (src/components/)

Each session stays <40k tokens. No cross-contamination.

**Handoff Docs pattern:**
```markdown
# Backend→Frontend Handoff

API endpoint: POST /api/auth/refresh
Request: { refreshToken: string }
Response: { accessToken: string, expiresIn: number }
Error codes: 401 (expired), 403 (revoked)
```

Session A generates → Session B reads via `@.claude/handoffs/auth-api.md`

## MCP vs CLI Token Economics

| Task | CLI Tokens | MCP Tokens | Multiplier |
|------|-----------|-----------|------------|
| Fetch repo metadata | 1,365 | 44,026 | 32x |
| Summarize merged PRs | 5,010 | 33,712 | 6.7x |
| List dependencies | 8,750 | 37,402 | 4.3x |
| Complex app discovery | 4,150 | 145,000 | 35x |
| Reliability | 100% | 72% | -28% |

**Root cause:** MCP loads JSON-RPC schema for ALL tools every turn, even if using one.  
43-tool GitHub MCP server = full schema ingested every single turn.

**Decision rule:**
- CLI (`git`, `gh`, `grep`, `npm`) → always prefer for dev tasks
- MCP → only when need per-user OAuth, enterprise governance, or live cloud data

**Warning:** Multiple MCP servers registered = majority of token budget consumed before first task.

## Session Isolation Checklist

Before starting a large task:
1. `/clear` to reset history
2. Provide concise state summary (not full history)
3. `@` only the files actually needed
4. `!` diagnostic commands to get current state
5. Use Plan Mode before implementation
6. Subagent for any exploration >20 files
