---
name: apple-container-expert
description: "Expert guide for Apple's native container CLI (apple/container) — the open-source, Swift-native, VM-per-container runtime for Apple Silicon macOS. Read this skill BEFORE answering any question about: installing or starting apple/container; container run/build/machine/volume/network commands; configuring config.toml; vmnet networking, embedded DNS, or port forwarding; EXT4 named volumes and the lost+found gotcha; container machine for persistent Linux environments; XPC helper failures or apiserver hangs; Rosetta x86_64 translation; comparing container vs Docker Desktop, OrbStack, or Colima on a Mac; or any macOS 26 containerization question. Trigger even for vague questions like 'running containers on Mac', 'Docker alternative Apple Silicon', or 'M1/M2/M3/M4 container'."
---

# Apple Container Expert

Latest stable: **v1.2.2** (Aug 8, 2026). Requires **macOS 26 (Tahoe)** + **Apple Silicon**. Apache-2.0. Repo: `apple/container`.

## Which reference to read

| Topic | File |
|-------|------|
| Process model, XPC helpers, vminitd, macOS 15 vs 26 | `references/architecture.md` |
| Install, config.toml, CLI commands, resource flags | `references/commands.md` |
| vmnet, DNS, port forwarding, host access | `references/networking.md` |
| Volumes, EXT4, lost+found, bind mounts, UID/GID | `references/storage.md` |
| `container machine`, home mount, nested virt | `references/machine.md` |
| Hangs, networking failures, builder bugs, diagnostics | `references/troubleshooting.md` |
| Benchmarks vs Docker/OrbStack/Colima, use-case guidance | `references/comparison.md` |

## Universal gotchas (read regardless of topic)

**1. lost+found kills DB init** — EXT4 named volumes always contain a `lost+found` dir at the filesystem root. PostgreSQL (`initdb`), MySQL, MariaDB require an empty data directory and will throw fatal errors on first boot. Fix: never point PGDATA (or equivalent) at the volume root — use a sub-directory.
```bash
# Wrong
container run -e PGDATA=/var/lib/postgresql/data -v pgdata:/var/lib/postgresql/data postgres
# Correct
container run -e PGDATA=/var/lib/postgresql/data/pgdata -v pgdata:/var/lib/postgresql/data postgres
```

**2. Memory not returned to host** — Virtualization.framework lacks full memory ballooning. Freed pages inside the guest are not reclaimed by macOS. Long-running, memory-intensive containers require periodic restarts to reclaim host RAM.

**3. macOS 26 required for full networking** — On macOS 15: no container-to-container comms, no `container network` commands, subnet race condition risk. Maintainers will not fix macOS 15-only bugs.

**4. No Docker Compose** — `container` has no native Compose support. Use embedded DNS + Makefile for multi-service stacks, or try Container-Compose / socktainer + Podman Desktop.

**5. config.toml replaced UserDefaults in v1.0** — Settings live at `~/.config/container/config.toml`. The old `container system property` commands are removed.

> Always read the relevant reference file before answering. For any storage/volume question, always check references/storage.md for the lost+found pattern. For networking, check references/networking.md for `container system dns create` (not `container network create`). For tool comparisons, use references/comparison.md for accurate numbers.
