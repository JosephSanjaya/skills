# Container Machine

`container machine` provides a **persistent Linux environment** — Apple's equivalent of WSL2, built on the same VM-per-container infrastructure.

## Key differences from `container run`

| Aspect | `container run` | `container machine` |
|--------|-----------------|---------------------|
| Lifecycle | Ephemeral — gone when stopped | Persistent — survives stop/start |
| Init system | `vminitd` (minimal, no systemd) | Image's own init (systemd, openrc) |
| Home directory | Not mounted | macOS `~` mounted read-write by default |
| Linux user | Container's user | Mirrors macOS account name |
| Sudo | N/A | Passwordless sudo granted automatically |
| Working directory | Container workdir | Synced to macOS current directory |

## Commands

```bash
container machine create dev ubuntu:24.04              # create machine named "dev"
container machine create dev ubuntu:24.04 --cpus 4 --memory 8g
container machine create dev ubuntu:24.04 --home-mount ro   # read-only home

container machine run dev                              # drop into interactive shell
container machine run dev -- bash -c "uname -a"       # run single command

container machine list                                 # list machines
container machine inspect dev                          # JSON metadata
container machine set -n dev cpus=4 memory=8g         # resize (applies on next restart)
container machine stop dev
container machine delete dev
container machine logs dev                             # init system + service logs
```

Alias: `m` = machine

## Home mount options

| Option | Flag | Security level | Use when |
|--------|------|---------------|----------|
| Read-write (default) | `--home-mount rw` | Lowest | Trusted personal dev environments |
| Read-only | `--home-mount ro` | Medium | Can read your files, not modify them |
| None | `--home-mount none` | Highest | Untrusted code, AI-generated scripts, 3rd-party packages |

**Security warning:** The default rw home mount exposes `~/.ssh`, credential files, and all home directory secrets to any package installed inside the machine. A malicious npm package or pip dependency could harvest your SSH keys. The VM boundary prevents guest root from becoming host root — but filesystem access is real. Use `ro` or `none` for any work involving untrusted dependencies.

## Default resource allocation

`--memory` defaults to **half of host RAM** (e.g., 32 GB on a 64 GB machine). Actual resident usage is far lower; community measurement found ~1 GB used after starting PostgreSQL.

## Setting up Ubuntu + systemd (reference)

Apple provides a reference Dockerfile. Build it and use as base:

```bash
# Build the Apple reference image (from apple/container repo docs)
container build -t ubuntu-systemd ./docs/tutorials/machine-example/

container machine create dev ubuntu-systemd --cpus 4 --memory 8g --home-mount ro
container machine run dev
# Inside: sudo apt install ... as normal Linux env
```

Any image with `/sbin/init` works.

## Nested virtualization (M3+ only)

Requirements: M3 or newer chip, macOS 15+, kernel built with `CONFIG_KVM=y` (default kernel does NOT have this — must supply a custom kernel).

```bash
container machine create --virtualization kvm-machine my-kvm-image
```

## Known rough edges (v1.0–v1.2)

- Username-mirroring race condition on first boot may cause login failure
- Home path inconsistency: docs reference `/home/<user>`, actual mount lands at `/Users/<user>`
- Passwordless sudo silently fails if macOS username contains a period (`.`)
- `container machine set` changes apply only on next restart, not immediately
