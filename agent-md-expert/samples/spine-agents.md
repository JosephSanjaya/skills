# AGENTS.md

> **Project:** Next.js + Bun + Turbo Monorepo
> **Core Fact:** isolated git-worktree workspace. "Workspace" means this directory, not editor workspace.

## Commands
| Intent | Command | Notes |
|:---|:---|:---|
| Install | `bun install` | Do not use npm/yarn/pnpm |
| Build | `bun run build` | Builds all packages via Turbo |
| Test (All) | `bun test` | Runs vitest/jest across all workspaces |
| Lint | `bun run lint:fix` | Biome — authority is `biome.json` at root |
| Typecheck | `bun run typecheck` | Strict TSC pass |

## Boundaries
**NEVER**
- Commit secrets, `.env` files, or production private keys.
- Create `middleware.ts` in Next.js (Next.js 16 uses `proxy.ts` for intercepting).
- Bypass the GitHub CLI (`gh`) for git operations where available.

**ASK**
- Before running database migrations (`drizzle-kit push`).
- Before modifying files in any `plans/` directory.

**ALWAYS**
- Run `bun run lint:fix` and verify it exits 0 before pushing.
- Write direct, early-return code without nested blocks.
