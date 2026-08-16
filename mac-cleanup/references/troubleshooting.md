# Stage 3 — Troubleshooting

Named symptom only. Not monthly hygiene. Routine cache wipes slow the next launch.

<instructions>
## DNS
Stale resolution after hosts/VPN change:
```
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```
Both halves required (Big Sur → Tahoe).

## Spotlight
Wrong/missing results only. Rebuild: 30min–hours.
```
!mdutil -s /
sudo mdutil -E /
```
Do not Trash `.Spotlight-V100`. Use `mdutil`, not manual deletes.

## User caches
`~/Library/Caches` regenerates. Broken app or post-update glitch → Safe Mode, not `rm /Library/Caches`.

Script `caches` (opt-in): contents of `~/Library/Caches` only.

## Crash reports
`~/Library/Logs/DiagnosticReports` ok. Never `/var/db/diagnostics`. Leave `/private/var/log/apache2/` dirs so Apache can start.

## launchctl
```
!launchctl list | grep -v com.apple
!launchctl bootout gui/$(id -u)/<label>
!launchctl disable gui/$(id -u)/<label>
sudo launchctl bootout system/<label>
```
After `disable`, `bootstrap` needs `enable` first. Settings → Login Items first.

## Memory vs purge
Activity Monitor → Memory Pressure. Free RAM holding cache is healthy. `sudo purge` cold-caches Apple silicon and does not fix yellow/red pressure — quit the greedy process.

## Safe Mode
Shift (Intel) or Startup Options (Apple silicon). After a bad update, not on a schedule.
</instructions>

<constraints>
- Output: one fix for the named symptom. Must not treat these as routine cleanup.
- Must not delete Unified Logs or `/Library/Caches`.
- Must use `bootout`/`disable`, not `unload`.
- Format: command + when to run it. `/clear` after the glitch is fixed.
</constraints>
