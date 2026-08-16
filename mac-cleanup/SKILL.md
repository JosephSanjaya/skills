---
name: mac-cleanup
description: "Clean and reclaim disk space on a Mac using native CLI tools and a dry-run-first script. Use whenever the user mentions Mac disk space, System Data bloat, purgeable space, Finder vs df mismatch, Time Machine local snapshots, Xcode DerivedData or simulators, Docker images, Homebrew/npm/pip/pnpm/yarn/go caches, leftover files after uninstalling an app, a slow Mac, or wants to clear caches, logs, or Trash on macOS. Prefer this skill over generic 'wipe caches' advice — modern macOS (Sonoma, Sequoia, Tahoe) already self-maintains, so the real wins are developer artifacts, stale backups, and snapshots, not deleting system caches or Unified Logs."
compatibility: "Requires macOS (darwin). scripts/cleanup.py needs Python 3.12+. Uses native tools when present (tmutil, diskutil, brew, docker, xcrun, npm, pip)."
---

# Mac Cleanup

macOS already reclaims caches, temp, and most purgeable space. Real wins: developer artifacts, snapshots, stale backups.

<instructions>
## Workflow
1. Audit: `!python3 scripts/cleanup.py` (dry-run). Numbers → @references/audit.md
2. Show plan. Wait for confirm.
3. Apply listed modules only: `!python3 scripts/cleanup.py --apply --modules brew,xcode,npm`
4. Re-audit.
5. Named symptom (Spotlight/DNS/caches) → @references/troubleshooting.md

@scripts/cleanup.py — default modules `brew,xcode,npm,pip,pnpm,yarn,go` (skip if missing). Opt-in: `docker,snapshots,trash,caches,crash-reports`. `--modules audit` = sizes only. `--aggressive` = Docker unused images, never volumes.

Deletes stay inside `$HOME` allowlist. No `sudo rm`, SIP paths, Unified Logs, `/private/var/folders`.

## References (load one)
| Need | File |
|------|------|
| Finder vs df, snapshots | @references/audit.md |
| Snapshots, brew, backups, login items | @references/safe-cleanup.md |
| Xcode, Docker, npm/pip/go | @references/developer-caches.md |
| Spotlight, DNS, caches, launchctl | @references/troubleshooting.md |
| periodic, purge, SIP, Unified Logs | @references/avoid.md |
</instructions>

<constraints>
- Output format: audit → plan → confirm → apply. Never `--apply` first.
- Must refuse SIP-off and `sudo rm` under `/System`, `/usr`, `/bin`, `/private/var/db`.
- Must not run `sudo periodic`, routine `purge`, or wipe `/Library/Caches`.
- Thin snapshots only if space is needed now and an off-device backup exists.
- Prefer native verbs (`brew cleanup`, `xcrun simctl`, `tmutil`) over hand `rm`.
- Load only the matching reference. `/clear` before a different task.
</constraints>
