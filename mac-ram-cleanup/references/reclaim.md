# Stage 2 — Reclaim

Fix the hog. Cheaper than fighting the compressor.

<instructions>
## Levers (order)
| # | Action |
|---|--------|
| 1 | Quit/restart top quittable (not `kernel_task`). RSS unchanged after quit → leak; restart that app. |
| 2 | Browser: Chrome/Brave Memory Saver; Edge Sleeping Tabs; ⌘Q not close-window; Safari if no Chromium needed. |
| 3 | Settings ▸ General ▸ Login Items & Extensions. Prefer Settings over editing `~/Library/LaunchAgents`. |
| 4 | Keep ~10–20% Data-volume free. Disk problem → **mac-cleanup**. |
| 5 | Uptime many days + yellow/red → reboot (clears leaks + swap files). |
| 6 | Wait out Spotlight `mds*` / Photos `photoanalysisd`. Spotlight privacy, not `mdutil -i off /`. |
| 7 | 8–16 GB: Reduce Transparency/Motion. Native display scale. |
| 8 | Builds: `jobs ≈ ram_giB/2` (~2 GiB/thread). 16 GiB → `make -j4`. |

| Cmd | Effect |
|-----|--------|
| `killall Finder` | Thumbnail cache. Restarts Finder. No logout. Consent. |
| App quit | Returns anonymous RSS. Consent. |

`sudo killall WindowServer` = GUI logout. Only if user accepts.

Leave App Nap on. "Close windows when quitting" helps ⌘Q+restore.

Hardware last: sustained red + high swap **rates** + beachballs at real work. Apple Silicon RAM soldered. 16 GB baseline; 24–32 GB VMs/LLM. Green → more RAM unused.
</instructions>

<constraints>
- Confirm before quit / `killall Finder`.
- Must not flush caches for a higher "free" number.
- Green → optional quits for headroom only (idle VM/browser), not because RAM looks full.
- `/clear` after the user picks a lever.
</constraints>
