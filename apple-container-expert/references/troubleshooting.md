# Troubleshooting & Diagnostics

## Diagnostic commands (run first)

```bash
container system status                            # API health check
container system version --format json             # version + XPC socket connectivity
container system df                                # storage utilization: images, layers, volumes
container system logs --last 30m                   # recent XPC helper + apiserver logs
container stats                                    # live: CPU%, memory vs limit, net Rx/Tx, block I/O, PIDs
container stats --no-stream --format json          # one-shot snapshot (scripting)
container logs <name>                              # container stdout/stderr
container logs --boot <name>                       # kernel boot + vminitd init logs (use when container won't start)
container inspect <name> | jq                      # full JSON: config, mounts, network, state
launchctl list | grep container                    # verify launchd processes are registered
log stream --predicate 'subsystem CONTAINS "com.apple.container"' --style compact
```

---

## Common failures

### `container system start` hangs at "Verifying apiserver is running..."

**Cause A:** Project or working directory is on an external or non-root disk (issue #621).
**Fix A:** Ctrl-C to interrupt (may leave system in wedged state requiring reboot). Move project to internal disk.

**Cause B:** Helper binaries located under `~/Documents` or `~/Desktop` — vmnet framework blocks them.
**Fix B:** Move the repository/project directory outside of `Documents` and `Desktop`.

**Recovery if wedged:**
```bash
container system stop    # may fail; try anyway
# if still stuck: reboot
container system start
```

### XPC connection error: Connection invalid

**Symptom:** `container ls` or any command returns `XPC connection error: Connection invalid`.
**Fix:** The apiserver isn't running. `container system start`.

### Networking dies after reboot or OS update

**Symptom:** Containers start but can't reach network; bridge subnet shifted (e.g., `192.168.64.1` → `192.168.65.1` or `192.168.66.1`).
**Fix:**
```bash
container system stop
# Edit ~/.config/container/config.toml: set network.subnet to the new /24 range
container system start
container builder rm -f    # clears stale /etc/resolv.conf in builder VM
```

### Network loss on macOS 15

**Cause:** `container-network-vmnet` initializes before vmnet establishes its interface — race condition.
**Fix:**
```bash
container stop -a
container system stop
container system start
```
If networking remains broken: use `--publish host_port:container_port` and connect via host gateway IP `192.168.64.1`.

### `container rm -f` fails with "config.json … no such file"

**Cause:** Container metadata directory corrupted (issue #1058).
**Fix:** Manually remove the state directory:
```bash
ls ~/.local/share/container/containers/
rm -rf ~/.local/share/container/containers/<container-id>
```

### Builder hangs after crashed build

**Symptom:** `container builder stop --force` returns immediately but builder remains stuck.
**Fix:** No soft workaround. Reboot required (issue #677).

### Builder can't pull packages (`apt-get`/`apk add` fails)

**Cause:** Builder VM lacks outbound network access in some network configurations.
**Fix:** Try `container system stop && container system start`. If persistent, check DNS config and network.subnet in config.toml.

### CLI / GUI reports "os error 2" (binary not found)

**Diagnosis:**
```bash
which container                  # expect /usr/local/bin/container
ls -la /usr/local/bin/container  # verify executable bit
container ls -a --format json    # verify structured JSON output
```
If missing: reinstall via `.pkg` from GitHub releases (not Homebrew on macOS 26).

### DNS failures

Active known bugs:
| Issue | Bug ID | Symptom |
|-------|--------|---------|
| dnsmasq/local port 53 conflict | #402 | DNS fails when something binds port 53 on a specific interface |
| System DNS breaks egress | #1241 | Using system DNS breaks all outbound traffic randomly |
| Clean install DNS failure | #856, #1693 | Internal DNS doesn't work on fresh install |
| UDP silent failure | #696 | UDP DNS queries silently drop; TCP works as workaround |

Check these issues before assuming configuration is wrong.

### DevContainers in VS Code

Partial support — gaps in networking and setup scripts. Check the apple/container issue tracker.
