# Stage 1 — Audit

Finder "Available" includes purgeable; `df` does not. Gap → snapshots, not a mystery `rm` target.

<instructions>
## Disk
```
!df -h /
!df -ih /
!diskutil apfs list
```
Judge free space at the APFS **container**. `df -l` skips NFS. `df` full + `du` free → `!lsof +L1`.

## Snapshots
```
!tmutil listlocalsnapshots /
!tmutil listlocalsnapshotdates /
!diskutil apfs listSnapshots /
```
Hourly locals ~24h, then macOS drops them. Third-party snapshots (CCC) are not purgeable — vendor deletes them.

## Heavy dirs
```
!du -sh ~/Library/Caches ~/Library/Developer ~/Library/Containers \
  ~/Library/Application\ Support/MobileSync/Backup \
  ~/Library/Developer/CoreSimulator 2>/dev/null | sort -h
```
Giants: DerivedData, CoreSimulator, Docker, brew cache, `node_modules`, iOS backups.

@scripts/cleanup.py already sizes these when tools exist.
</instructions>

<constraints>
- Apple Intelligence models: Settings off + restart. Never `rm` AssetsV2.
- Post-upgrade System Data bloat 24–48h is normal; reboot before treating as permanent.
- Output: numbers only. No deletes this stage.
- Must not `rm` `/System/Volumes/Data` or chase purgeable space.
</constraints>
