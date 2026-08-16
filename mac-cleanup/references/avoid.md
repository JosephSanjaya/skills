# Do not

<instructions>
## Removed / useless
| Advice | Why |
|--------|-----|
| `sudo periodic daily weekly monthly` | Removed in Sequoia. `logd` handles attrition. |
| Routine `sudo purge` | Cold cache; benchmarking only. |
| Repair permissions | Gone. |
| Chase purgeable (dummy files, cache wipes) | Reclaimed automatically. |
| Delete `/var/db/diagnostics` or `/var/db/uuidtext` | Unified Log DB. `logd` keeps Persist ~500MB / diagnostics ~1.5GB. |
| `sudo rm -rf /Library/Caches/*` as hygiene | Slows every app. |
| `launchctl load` / `unload` | Deprecated. Use `bootstrap`/`bootout`. |

## Dangerous
- `sudo rm -rf` on system paths. A stray `/` or `/System/Volumes/Data` is catastrophic. SIP may save the sealed volume; not the Data volume.
- `csrutil disable` / authenticated-root to "clean." Sealed snapshot; skip `bless --create-snapshot` → unbootable. Leave SIP on (`!csrutil status`).
- `rm` Apple Intelligence models under `/System/Library/AssetsV2`. Settings off + restart.
- Treat `/System/Volumes/Data` as junk — it is the writable volume.
- Delete `/private/var/db` or `/private/var/folders`. Receipts are for *finding* leftovers, not deletion.
- `docker system prune -a --volumes` without explicit volume-loss consent.
- `curl \| bash` cleaners. Prefer @scripts/cleanup.py or audited `mac-cleanup-py`. Skip opaque one-click apps.
</instructions>

<constraints>
- Output: refuse the unsafe path, then redirect to audit → developer caches → snapshots with backup.
- Must not disable SIP or invent `rm` recipes for `/System`.
- Must not delete Unified Logs.
- Format: short refusal + the safe alternative. `/clear` after the user picks a safe module list.
</constraints>
