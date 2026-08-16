# Developer caches

Usually the largest reclaim. Script runs a tool only if it is on `PATH`.

<instructions>
## Xcode / simulators
```
rm -rf ~/Library/Developer/Xcode/DerivedData/*   # contents only; rebuild cost
!xcrun simctl delete unavailable                 # after Xcode upgrades
!xcrun simctl runtime delete unavailable
!xcrun simctl runtime delete --notUsedSinceDays 90
```
Also large: Archives, iOS DeviceSupport, CoreSimulator. SIP-protected runtimes under `/System/Library/AssetsV2` → `xcrun simctl runtime`, not `rm`.

`simctl erase all` wipes simulator content — only if the user wants a clean slate.

Script `xcode`: size DerivedData, delete contents on `--apply`, `simctl delete unavailable`.

## Docker
```
docker info >/dev/null || return
!docker system df
!docker builder prune -f
!docker system prune -f          # dangling only
!docker system prune -a -f       # unused images; never --volumes unless user accepts data loss
```
Script `docker` = dangling + builder. `--aggressive` adds `-a`. Volumes stay unless asked.

## JS / Python / Go / brew
```
!npm cache clean --force
!pnpm store prune
!yarn cache clean
!pip cache purge
!go clean -cache
!brew cleanup -s && brew autoremove
!find ~ -name node_modules -type d -prune -print
```
Do not recursively delete every `node_modules` without confirm.
</instructions>

<constraints>
- Output: per-tool sizes + skip reasons. Confirm before `--apply`.
- Must not `docker system prune --volumes` unless the user accepts volume loss.
- Must not `rm` SIP-protected simulator runtimes.
- Format: native CLIs over hand `rm` except DerivedData contents.
</constraints>
