# Mobile DevOps Reference

## Challenges

| Challenge | Why Hard |
|---|---|
| Code signing | Certs, provisioning profiles, entitlements — each platform different |
| Proprietary build env | iOS requires macOS + Xcode; no Linux alternative |
| Interactive auth | Apple 2FA prompts break headless CI runners |
| OEM hardware bugs | Emulators miss vendor-specific rendering/driver issues |

---

## Fastlane Match (iOS Code Signing)

Centralizes certs in encrypted Git repo or GitLab Secure Files. Single source of truth — eliminates "works on my machine" cert chaos.

### Matchfile

```ruby
gitlab_project("org/mobile-delivery/app")
storage_mode("gitlab_secure_files")
type("appstore")
```

### Migration Strategy

1. Schedule planned maintenance window
2. Revoke all existing certs
3. Run `match` to regenerate single source of truth
4. Distribute new profiles automatically

> [!WARNING]
> Breaks local builds temporarily during migration. Coordinate with team.

---

## Fastfile (iOS)

```ruby
platform :ios do
  lane :release do
    setup_ci                              # Temp keychain for CI
    match(type: 'appstore', readonly: is_ci) # Never mutate certs from CI
    build_app(
      clean: true,
      project: "App.xcodeproj",
      scheme: "Production",
      export_method: "app-store"
    )
    upload_to_testflight(
      skip_waiting_for_build_processing: true,
      apple_id: ENV['APPLE_ID']
    )
  end
end
```

Critical: `readonly: is_ci` — prevents CI from mutating/revoking production certs. CI only reads, never writes.

---

## Fastfile (Android)

```ruby
platform :android do
  lane :release do
    gradle(
      task: 'bundle',         # AAB format (mandated by Google Play)
      build_type: 'Release',
      properties: {
        "android.injected.signing.store.file" => ENV['KEYSTORE_PATH'],
        "android.injected.signing.store.password" => ENV['KEYSTORE_PASSWORD'],
        "android.injected.signing.key.alias" => ENV['KEY_ALIAS'],
        "android.injected.signing.key.password" => ENV['KEY_PASSWORD']
      }
    )
    upload_to_play_store(
      track: 'internal',
      skip_upload_apk: true   # AAB only, no legacy APK
    )
  end
end
```

Signing creds injected via env vars — never hardcoded in repo.

---

## Authentication

| Platform | Method | Why |
|---|---|---|
| iOS | App Store Connect API keys | Bypasses 2FA entirely; headless-safe |
| Android | Google Play Service Account JSON | Service account = no interactive login |

> [!IMPORTANT]
> Never use personal Apple ID with 2FA on CI. Will hang/timeout waiting for interactive prompt.

---

## Advanced Testing

| Tier | Method | Coverage |
|---|---|---|
| Standard CI | Software emulators | Fast, cheap; misses OEM bugs |
| Advanced | Real-device cloud (Firebase Test Lab, BrowserStack) | Catches vendor-specific rendering/driver issues |

Gate deployment on physical hardware UI validation for critical releases. Emulator-only pipelines miss real-world failures.

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Manual cert distribution | Fragile, "works on my machine" | Use Fastlane Match |
| Apple ID + 2FA on CI | Hangs/timeouts on headless runner | App Store Connect API keys |
| Building APK instead of AAB | Rejected by Google Play | `task: 'bundle'` in Fastfile |
| CI mutating production certs (`readonly: false`) | Accidental revocation breaks all builds | `readonly: is_ci` always |
| Hardcoded signing credentials | Leaked secrets in repo history | Inject via CI env vars / vault |
