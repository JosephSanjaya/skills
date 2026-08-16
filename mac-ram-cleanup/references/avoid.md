# Do not (RAM)

Fighting the compressor slows the next minutes. Free RAM is not a goal.

<instructions>
## Placebo / harmful
| Advice | Why |
|--------|-----|
| RAM cleaners (CleanMyMac RAM, Memory Clean, …) | malloc-spam to purge caches; refill from disk. I/O, CPU, battery. Vendor roundups = marketing. |
| Routine `sudo purge` | File cache only. Not malloc/swap/leaks. Man page: no anonymous memory. Cold-cache benchmark. |
| `memory_pressure -l warn\|critical` | *Creates* pressure. Never cleanup. |
| Chase 0 swap / lots of free RAM | Kernel parks idle anonymous pages so cache keeps DRAM. Static swap on green = intentional. |
| `nvram boot-args=… vm_compressor=1\|2` | Unsupported. Kernel forces Mode 4. No-swap → panic/Jetsam. |
| Disable SIP to "tune" VM | Unrelated. Leave SIP on (`!csrutil status`). |

## Dangerous
- `sudo killall WindowServer` as RAM fix — ends the login session.
- `sudo mdutil -i off /` — breaks search. Use Spotlight privacy.
- Kill `kernel_task` — you cannot.
- Hand-edit BTM DB. Use Settings ▸ Login Items.

A live **monitor** (Activity Monitor, iStat) is fine. Observe, don't "clean".
</instructions>

<constraints>
- Output: short refusal, then diagnose → quit the real hog.
- Must not run/install RAM cleaners.
- Must not invoke `purge` or `memory_pressure -l`.
- Must not change compressor/swap sysctls or boot-args.
- `/clear` after refusal.
</constraints>
