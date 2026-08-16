---
name: mac-ram-cleanup
description: "Diagnose and reduce macOS RAM pressure using kernel telemetry (memory pressure, compressor, swap rates), not fake 'free RAM'. Use whenever the user mentions Mac RAM, memory pressure, swap used, compressed memory, Activity Monitor Memory tab, a sluggish Mac with RAM full, RAM cleaners, sudo purge, kernel_task or WindowServer memory, Chrome/browser RAM, Docker Desktop RAM, Finder using gigabytes, or wants to clean/optimize Mac memory. Prefer this over mac-cleanup when the complaint is RAM/swap/pressure rather than disk space. Green pressure means do nothing — unused RAM is wasted RAM."
compatibility: "Requires macOS (darwin). scripts/diagnose.py needs Python 3.12+. Read-only: vm_stat, sysctl, ps, df, memory_pressure. Never calls purge or RAM-cleaner allocators."
---

# Mac RAM Cleanup

macOS fills RAM (cache + compression). Gauge = **pressure**, not free bytes.

<instructions>
## Workflow
1. `!python3 scripts/diagnose.py` (`--json` ok) → @references/diagnose.md
2. Green / kernel 0 / swapout_delta 0 → stop. Full RAM = cache, not a leak.
3. Yellow/red or swapouts → top quittable hog → @references/reclaim.md
4. Named hog (kernel_task, WindowServer, Finder, Spotlight, Photos, Docker, leak) → @references/edge-cases.md
5. Cleaners / `purge` / disable swap / SIP-off → @references/avoid.md

Disk / System Data / snapshots → **mac-cleanup**. Data volume <15% free still blocks swap here.

@scripts/diagnose.py read-only: 2× `vm_stat` rates, `vm.swapusage`, `vm.memory_pressure`, top RSS, disk headroom. No `--apply`.

## References (load one)
| Need | File |
|------|------|
| pressure, vm_stat, page size | @references/diagnose.md |
| quit, browser, login items, reboot | @references/reclaim.md |
| cleaners, purge, compressor_mode | @references/avoid.md |
| kernel_task, WindowServer, Docker, UMA | @references/edge-cases.md |
</instructions>

<constraints>
- Output: diagnose → act only if yellow/red or thrashing. Never "clean RAM" first.
- Must not run `sudo purge`, RAM cleaners, `memory_pressure -l`, malloc-spam.
- No `nvram boot-args`, `vm.compressor_mode`, disable swap/compression.
- No `sudo killall WindowServer` unless user accepts GUI logout.
- `killall Finder` only with consent.
- `memory_pressure` free% = cache headroom, not the pressure graph.
- Must load one reference only. `/clear` before a different task.
</constraints>
