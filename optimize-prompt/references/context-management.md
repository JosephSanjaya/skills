---
name: context-management
description: Context window mechanics, slash commands, session hygiene, CLAUDE.md architecture, and compaction strategy
metadata:
  type: reference
---

# Context Management

## Window Budget Reality

| Component | Token Range | % of 200k |
|-----------|-------------|-----------|
| System Prompt + CLAUDE.md | 3k–8k | 2–4% |
| Auto-read source files | 10k–50k | 5–25% |
| Conversation history | 30k–120k | 15–60% |
| Model response generation | 5k–20k | 3–10% |
| Tool call outputs (logs/tests) | 10k–80k | 5–40% |

Saturation = ~15–20 turns in complex debug sessions.  
At saturation: agent ignores early instructions, repeats corrected mistakes, over-engineers.

---

## Context Window Economics

| Session Phase | Baseline Tokens | Optimized Tokens | Reduction Method |
|--------------|----------------|------------------|------------------|
| Initial Setup | 1,000-2,000 | 300-600 | Global CLAUDE.md + MCP |
| Mid-Session (Turn 15) | 15,000-25,000 | 4,000-7,000 | /compact + selective context |
| Late-Session (Turn 30) | 50,000+ | 12,000-15,000 | Session forking + prefix caching |
| Task Transition | 75,000 | 500 | Context reset with state transfer |

---

## Slash Commands — Priority Order

| Command | Function | When |
|---------|----------|------|
| `/clear` | 100% token recovery | After every discrete subtask |
| `/compact` | Summarize history (~60% recovery) | At natural task boundaries |
| `/rewind` | Revert to checkpoint | Agent produced over-engineered/buggy output |
| `/usage` | Show token consumption graph | Before large multi-file refactor |
| `/btw` | Side-chat (doesn't bloat main history) | Quick clarifications |

**Primary rule:** `/clear` after every successful unit of work + provide concise state summary in next prompt. Saves 80–90% over long sessions.

---

## Session Reset Guidelines
- **Conversation Reset Frequency**: Reset every 15-20 messages. History tax compounds exponentially. By turn 30, even trivial instructions can cost 50k+ tokens.
- **State Transfer**: When resetting with `/clear`, use the Post-Clear Summary Template to transfer state.
- **Memory Profiling**: Use `/context` to identify large files or tool definitions consuming context, and evict no-longer-required items.

---

## Post-Clear Summary Template

```
State: [what was just completed]
Files changed: [list]
Next task: [specific goal]
Context: @[relevant files only]
```

---

## CLAUDE.md Architecture

**Optimal size:** <200 lines. Over 200 lines = costs more in input tokens than it saves.

**Include:**
- Non-obvious architectural decisions
- Preferred test runners / build commands  
- Dev environment quirks (non-standard paths, required env vars)
- Hard constraints (ES modules not CommonJS, no mocking in integration tests)

**Exclude:**
- Standard language conventions (Claude already knows these)
- Documentation (that's for humans, not agents)
- Long examples (put in references/ with @-reference)

**Treat as lookup table, not docs.**

---

## Path-Scoped Rules (.claude/rules/)

YAML frontmatter with `paths` key = just-in-time context delivery.

```yaml
---
paths: ["src/components/**"]
---
# React frontend rules
- Use Tailwind, no inline styles
- Components must have error boundaries
```

Rules for Go backend never loaded when editing React files. Preserves context for reasoning.

---

## Compaction Strategy

Default threshold 95% → set to 85% in settings.json:
```json
{ "compactionThreshold": 0.85 }
```
Reduces response time ~2.3s in high-density sessions. Prevents attention degradation near full window.

**PreCompact hook** — snapshot critical state before compaction wipes it:
```json
{
  "hooks": {
    "PreCompact": [{
      "command": "cat .claude/current-plan.md >> .claude/snapshots/$(date +%s).md"
    }]
  }
}
```

**PostToolUse hook** — auto-format after every edit:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "command": "prettier --write $CLAUDE_TOOL_OUTPUT_FILE 2>/dev/null || true"
    }]
  }
}
```

---

## Plan Mode

Activate: `Shift+Tab` in terminal.

- Lighter model for exploration phase → ~50% token reduction in discovery
- Agent proposes plan without modifying files
- Correcting a plan << unwinding half-finished implementation

**First Step Rule:** After plan approval, ask for step 1 only. Review → step 2. Never "implement the whole feature."
