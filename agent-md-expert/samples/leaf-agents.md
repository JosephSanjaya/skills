# AGENTS.md (Desktop App Leaf)

## Commands
| Intent | Command | Notes |
|:---|:---|:---|
| Dev | `bun dev --filter=desktop` | Launches Electron app with HMR |
| Build | `bun run build --filter=desktop` | Packages app via electron-builder |
| Test | `bun test --filter=desktop` | Runs Playwright integration tests |

## local-constraints
- **trpc-electron Subscriptions:** `trpc-electron` only supports observables. Never use async generators for procedures under `src/lib/trpc/subscriptions/`.
- **Selectable Errors:** Errors rendered in the UI must have class `select-text cursor-text` because renderer body defaults to `user-select: none`.
