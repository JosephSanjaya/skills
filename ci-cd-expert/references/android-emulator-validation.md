# Local Pre-Merge Validation & Emulator

## Git Hooks with Gradle Auto-Install

Auto-copies hooks on every build — no manual install required per developer.

```kotlin
// root build.gradle.kts
tasks.register<Copy>("installLocalGitHooks") {
    description = "Copies and configures local Git hooks from scripts to the .git directory."
    from(File(rootProject.rootDir, "scripts/pre-push"))
    into(File(rootProject.rootDir, ".git/hooks"))
    fileMode = 0x1FD // octal 0755 — grants execution permissions
}

tasks.named("build") {
    dependsOn("installLocalGitHooks")
}
```

See `scripts/pre-push` for the hook script.

## Spotless ratchetFrom

Limits style checks to files changed relative to target branch — doesn't reformat untouched legacy code.

Note: `ratchetFrom` doesn't differentiate staged vs unstaged. For local pre-commit, use `git diff --staged` in hook instead.

## nektos/act — Local Action Dry-Run

Run GitHub Actions locally via Docker. Zero remote billing minutes.

**Problem**: Standard act Docker images (`catthehacker/ubuntu:act-latest`) lack Android SDK → `SDK location not found` errors.

**Fix**: Conditional SDK setup via `ACT` env var:
```yaml
- name: Set up Android SDK
  if: ${{ env.ACT }}
  uses: android-actions/setup-android@v4
  with:
    api-level: 34
```

Step runs only in local act runs; skipped on GitHub-hosted runners where SDK already present.

**.env file for act**:
```
ANDROID_HOME=/root/.android/sdk
GITHUB_TOKEN=ghp_exampleTokenValue
SOME_API_KEY="\"staged_key_value\""
```

**Run locally**:
```bash
act pull_request --env-file .env --artifact-server-path /tmp/artifacts
```

**macOS/Windows bypass Docker**:
```bash
act -P macos-latest=-self-hosted
```

## KVM Hardware Acceleration for Emulators

Without KVM → software translation → slow, timeouts, inflated billing. Standard 2-vCPU Linux runners support nested KVM.

```yaml
- name: Enable KVM group permissions
  run: |
    echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger --name-match=kvm
```

Run before `reactivecircus/android-emulator-runner`.

**Stable emulator config**:
- **Relative backing paths**: `qemu-img rebase -u -F qcow2 -b userdata-qemu.img userdata-qemu.img.qcow2` — ensures snapshot runs on arbitrary runner paths
- **SWANGLE rendering**: force software-accelerated rendering overlay when setting up snapshot credentials → prevents UI-rendering engine crashes

## Verification Tier Summary

| Tier | Platform | Scope | Billing Impact | Tooling |
|------|----------|-------|----------------|---------|
| Local Git Hooks | Developer host | Staged files | Zero | Git hooks, Spotless, ktlint, Gradle tasks |
| Local act dry-run | Docker on dev machine | Workflow steps | Zero | nektos/act, Docker Desktop, .env |
| CI (PR) | GitHub Actions VM | Full codebase | Consumes free monthly minutes | GitHub runner, KVM, setup-gradle |
