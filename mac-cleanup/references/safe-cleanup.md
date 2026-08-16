# Stage 2 — Safe cleanup

After audit + user confirm. Prefer `!python3 scripts/cleanup.py --apply --modules …`.

<instructions>
## Snapshots (opt-in)
Need space *now* + off-device backup exists:
```
!tmutil thinlocalsnapshots / 100000000000 4
sudo tmutil deletelocalsnapshots YYYY-MM-DD-HHMMSS
```
Args: path, bytes, urgency 1–4. Stop refill: Time Machine → Manual, or `sudo tmutil disable` (~30s) then `enable`.

Script: `--apply --modules snapshots --thin-bytes 100000000000`

## Homebrew
```
!brew cleanup -n
!brew cleanup -s && brew autoremove
```
Skip `brew upgrade` unless asked.

## iOS backups
`~/Library/Application Support/MobileSync/Backup/` — Finder → Manage Backups, or Settings → Storage → iOS Files. Keep latest. Local ≠ iCloud.

## Login items / agents
Settings → Login Items first, then:
```
!launchctl bootout gui/$(id -u)/<label>
!launchctl disable gui/$(id -u)/<label>
```
`load`/`unload` deprecated on Apple silicon. Disable, watch, then delete plist. Leave `com.apple.*` (SIP).

## Trash
Opt-in: `--modules trash`.

## App leftovers
Search, then confirm:
```
!mdfind "kMDItemCFBundleIdentifier == 'com.vendor.app'"
!find ~/Library -iname '*AppName*'
```
Sweep: Application Support, Preferences, Caches, Containers, Saved State, LaunchAgents, Logs, HTTPStorages. Security/cloud tools: vendor uninstaller only.
</instructions>

<constraints>
- Output: proposed modules + sizes. Require confirm before `--apply`.
- Must not delete snapshots without an off-device backup.
- Must use `bootout`/`disable`, not `unload`.
- Format: native verbs over hand `rm`.
</constraints>
