# Monorepo: Spine & Leaf Architecture

## Precedence Hierarchy
When multiple instruction sources exist, coding agents prioritize them in this sequence:
```
LLM System Prompt (lowest precedence / global)
  └── Agent System Prompt
        └── User Prompt (active session instruction)
              └── Leaf (subdir) AGENTS.md / CLAUDE.md
                    └── Spine (root) AGENTS.md / CLAUDE.md (highest precedence / local default)
```
*Note: A direct instruction in a leaf context file overrides the corresponding rule in the root spine file.*

## Spine vs. Leaf Roles

### Spine (Root File)
- **Scope:** Repository-wide defaults.
- **Content:** Package manager specification (e.g. `bun`, `pnpm`), global linting rules, security boundaries (e.g. "never commit `.env`"), and shared domain vocabulary.
- **Cache Strategy:** Highly static. Changes to this file should be rare to maximize KV prefix cache hit rates for all sessions.

### Leaf (Subdirectory File)
- **Scope:** Package-specific or module-specific boundaries.
- **Content:** Exact test command for the subdirectory, framework-specific tricks (e.g. "Next.js 16 named middleware to `proxy.ts`", "Electron IPC subscriptions must use observable pattern"), and local data-layer requirements.
- **Location:** Place at the root of sub-packages or services (e.g. `apps/web/AGENTS.md`, `packages/db/AGENTS.md`).

## Cross-Tool Bridging (CLAUDE.md vs. AGENTS.md)
Different AI agents search for different filenames by default:
- **Claude Code:** Walks up the directory tree looking for `CLAUDE.md`.
- **Cursor / Codex / Windsurf:** Search for `AGENTS.md` (or `.cursorrules`).

### Integration Strategy
1. **Root Symlink or Import:** Place core instructions in `AGENTS.md` (the cross-tool standard). Bridge to Claude Code by writing a one-line `CLAUDE.md` file importing it:
   ```md
   @AGENTS.md
   ```
   Alternatively, create a symlink:
   ```bash
   ln -s AGENTS.md CLAUDE.md
   ```
2. **Directory Symlinks:** In monorepos, symlink local agent configs so all tools discover the same directives (e.g., symlink `.claude/skills` to `.agents/skills`).
