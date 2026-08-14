# Commands & Configuration

## Install

```bash
brew install --cask container            # or download signed .pkg from GitHub releases
container system start                   # first launch; downloads default Linux kernel automatically
container run --rm alpine echo hello     # verify working
```

## Upgrade / downgrade / uninstall

```bash
container system stop
/usr/local/bin/update-container.sh               # upgrade to latest
/usr/local/bin/update-container.sh -v 1.1.0      # specific version
/usr/local/bin/uninstall-container.sh            # uninstall (-k keep data, -d delete data)
```

Avoid reinstalling via Homebrew on macOS 26 — shows Tier-2 warning and can break `container system start` (issue #561). Use the signed `.pkg` from GitHub releases.

## System commands

| Command | Description |
|---------|-------------|
| `container system start` | Register + launch launchd agents; prompt kernel download if needed |
| `container system stop` | Unregister + halt all daemons |
| `container system status` | API health check |
| `container system df` | Host storage: images, layers, volumes |
| `container system version --format json` | Verify API connectivity + version |
| `container system logs --last 30m` | Recent unified log entries from XPC helpers |

## config.toml

`~/.config/container/config.toml` (user) overrides `/etc/container/config.toml` (system). Changes require `container system stop && container system start` — no live reload.

```toml
[build]
cpus = 4
memory = "8g"
rosetta = true          # Rosetta for amd64 builds (default true)

[container]
cpus = 2
memory = "2g"

[dns]
domain = "local.developer"

[kernel]
# path to custom kernel binary

[network]
subnet = "192.168.64.0/24"
subnetv6 = "fd00::/64"

[registry]
default = "docker.io"
scheme = "auto"          # http, https, auto
max_concurrent_downloads = 5

[vminit]
# custom vminitd settings
```

## Container lifecycle

```bash
container run --rm -it alpine sh
container run -d --name web -p 8080:80 nginx
container create --name db postgres         # create without starting
container start db
container stop db
container kill db                           # SIGKILL
container rm db
container rm -f db                          # force-remove running container
container exec -it web sh
container logs web                          # stdout/stderr
container logs --boot web                   # kernel boot + vminitd init logs
container inspect web | jq                  # full JSON metadata
container stats                             # live: CPU%, mem, net I/O, block I/O, PIDs
container stats --no-stream                 # snapshot
container stats --format json
container cp ./file web:/path/in/container  # copy file into container
container cp web:/path/in/container ./file  # copy file out of container
container ls                                # running containers
container ls -a                             # all containers
container ls -a --format json               # scripting
```

## Resource flags

| Flag | Syntax | Notes |
|------|--------|-------|
| `--cpus` / `-c` | `--cpus 4` | Integer vCPU count (default: 2 from config or 1) |
| `--memory` / `-m` | `--memory 4g` | Granularity: 512M, 4G, 16G; freed pages not returned to host |
| `--shm-size` | `--shm-size 512m` | Shared memory |
| `--tmpfs` | `--tmpfs /tmp` | tmpfs mount inside container |
| `--init` | flag | Lightweight PID 1: zombie reaping + signal forwarding |
| `--rosetta` | flag | Enable Rosetta 2 x86_64 translation in guest |
| `--virtualization` | flag | Pass CPU virt extensions to guest (nested virt; requires M3+) |
| `--ssh` | flag | Forward macOS SSH_AUTH_SOCK into container |
| `--stop-signal` | `--stop-signal SIGTERM` | Override default stop signal |
| `--platform` | `--platform linux/amd64` | Force architecture for pull/run |

## Builder

```bash
container build -t myimage:latest .
container build --arch arm64 --arch amd64 -t myimage:latest .   # multi-arch
container build --no-cache -t myimage .

# Size up before heavy builds (defaults: 2 GiB RAM, 2 CPUs)
container builder start --cpus 8 --memory 32g
# If builder is already running:
container builder stop && container builder delete && container builder start --cpus 8 --memory 32g
container builder rm -f    # force remove (also clears stale /etc/resolv.conf)
```

Builder uses BuildKit. Standard Dockerfiles work. Note: builder lacks outbound network access in some configurations — `apt-get`/`apk add` may fail during build.

## Registry

```bash
container registry login --username <user> docker.io   # use PAT; credentials in Keychain
container registry login --username <user> ghcr.io
container images                                        # local images
container image pull ubuntu:24.04
container image rm myimage
container image tag myimage:latest myimage:v1.0
container image push myimage:latest
```

## Command aliases

`i` = image, `r` = registry, `v` = volume, `n` = network, `s` = system, `m` = machine

> Key: default container resources = 1 GiB RAM + 4 CPUs. Builder = 2 GiB + 2 CPUs. Config at `~/.config/container/config.toml` — requires stop/start to reload.
