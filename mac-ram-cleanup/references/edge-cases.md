# Edge cases

Judge with pressure. Big RSS ≠ bug.

<instructions>
## Hogs
| Process | Act |
|---------|-----|
| `kernel_task` | Don't chase RSS. High CPU often thermal, not RAM. |
| `WindowServer` | Reduce Transparency/Motion; native res. `killall WindowServer` logs out. Long uptime → reboot. |
| Finder | Gallery/Icon cache, days. Not a leak. `killall Finder` if need DRAM now. |
| Chrome/Edge/Arc/Brave/Firefox | Memory Saver / Sleeping Tabs; fewer tabs; Safari if possible. |
| `mds*` | Spotlight after updates/imports. Wait. Privacy exclusions, not `mdutil -i off /`. |
| `photoanalysisd` / `photolibraryd` | Idle + plugged in. Corrupt Syndication → Photos repair. |
| `bird` / `cloudd` | iCloud burst. Transient. |
| Docker Desktop | Static Linux VM + Electron (~1.5 GiB idle). Stop when unused. Daily containers → OrbStack/Podman. `node_modules` in named volume. |
| OrbStack | Dynamic VZ RAM. Quit VM if you need the memory. |
| VMware/Parallels/QEMU/`Virtualization` | Guest RAM = host RSS. Quit unused VMs. |
| Mail / Pages | Real leaks on huge mailboxes/docs. Quit/restart. |

## UMA / leaks / Jetsam
Apple Silicon: CPU+GPU+ANE one pool. 8 GB AS tighter than 8 GB Intel+VRAM. Don't 1:1 map Intel 16+8 VRAM → M-series 16.

Leak = RSS climbs in the *same* workflow, never drops until quit, pressure yellow/red. Then `!vmmap -summary <pid>` → `!leaks <pid>` (framework false positives common).

Jetsam ("out of application memory"): compressor+swap exhausted. Reboot, then find unbounded app. Disabling swap makes Jetsam more likely.

Normal swap I/O is not a practical SSD killer. Don't disable swap to "save the disk".
</instructions>

<constraints>
- Must not treat `kernel_task` or Cached Files as cleanup targets.
- Docker `prune` = disk (**mac-cleanup**). RAM lever = stop the VM.
- Hardware upgrade only after sustained red + swap *rates* under real work.
- `/clear` after the named hog is handled.
</constraints>
