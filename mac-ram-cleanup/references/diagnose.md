# Stage 1 — Diagnose

Pressure, not occupancy. 47/48 GiB used + green = healthy.

<instructions>
## Signals
| Signal | Source | Meaning |
|--------|--------|---------|
| Pressure color | Activity Monitor ▸ Memory | Green=ok. Yellow=compress/swap up. Red=suffering. Red at idle → leak or too little RAM. |
| `vm.memory_pressure` | `!sysctl vm.memory_pressure` | `0`=none. Non-zero=elevated. No published color cutoffs. |
| Swap **rate** | `vm_stat` Swapouts Δ ~2s | Static swap on green = normal. Rising swapouts = thrashing. |
| `vm.swapusage` | `!sysctl vm.swapusage` | `total`=high-water (until reboot). `used`=live. Encrypted. |

@scripts/diagnose.py: trust `pressure_band` + `swapout_delta`. Ignore large Compressed alone.

## Not leaks
- Cached Files / file-backed: instant reclaim.
- Compressed: in-RAM WKdm/LZ4. ~1.5–2.5× stored/occupied. Normal.
- `memory_pressure` last line = free%, **not** the graph.
- Page size: 16384 B Apple Silicon, 4096 B Intel. Multiply `vm_stat` counts.
- `kernel_task` multi-GB RSS: bookkeeping. Judge by pressure.

## Read-only
```
!vm_stat
!sysctl vm.swapusage vm.memory_pressure hw.memsize hw.pagesize
!memory_pressure
!ps -axo pid=,rss=,command=
```
`ps` > `top -l 1 -o mem` for parse. `footprint`/`vmmap`/`leaks` after a PID, often root.

Boot-cumulative Swapouts ≠ urgency. `--sample-seconds` (default 2). Swapouts in window ⇒ act. Else + pressure 0 ⇒ stop.
</instructions>

<constraints>
- Output: band, kernel index, swap used vs rate, compressor, disk, top RSS/families.
- Must not free cache to drop "Memory Used".
- Must not `memory_pressure -l` (simulates pressure).
- Intel vs Apple Silicon: same flow; page size + UMA → @references/edge-cases.md
- `/clear` after diagnose.
</constraints>
