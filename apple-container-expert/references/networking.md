# Networking

## Default network

- Subnet: `192.168.64.0/24`, gateway `192.168.64.1`
- Each container gets a **dedicated IP** on a shared vmnet bridge — managed by `container-network-vmnet` XPC helper
- Direct IP access from host works without port forwarding

## Embedded DNS (service discovery)

The primary service-discovery mechanism — equivalent to Compose's internal DNS, without YAML.

```bash
sudo container system dns create test              # creates /etc/resolver/test on macOS host
container run -d --name api myimage                # resolves as api.test from host + other containers
container run -d --name db postgres                # resolves as db.test
```

Named containers resolve as `<name>.<domain>`. Works for host-to-container and container-to-container (macOS 26 only; container-to-container is blocked on macOS 15).

## Port forwarding to localhost

```bash
container run -p 8080:80 nginx                     # 0.0.0.0:8080 → container:80
container run -p 127.0.0.1:8080:80 nginx           # bind to specific interface
container run -p 8080:80/tcp -p 9090:9090/udp nginx # mixed protocols
container run -p '[::1]:8080:80' nginx              # IPv6
```

Port forwards route to the first network's interface if container has multiple networks.

## Accessing host services from a container

```bash
sudo container system dns create host.container.internal --localhost 203.0.113.113
```

Use a documentation/private IP range (e.g., 203.0.113.x from TEST-NET-3) to avoid conflicts.

**Caveats:**
- Creating a localhost domain **disables iCloud Private Relay**
- The packet-filter rule is **removed on reboot** — must recreate after every restart
- Note: apple/container uses singular `host.container.internal`; Podman uses `host.containers.internal`

## Isolated networks (macOS 26 only)

```bash
container network create mynet --subnet 10.0.1.0/24 --subnet-v6 fd01::/64
container run --network mynet myimage
container network ls
container network rm mynet
container run --network default,mac=aa:bb:cc:dd:ee:ff myimage   # custom MAC address
```

Networks are mutually isolated. `--network` flag returns fatal error on macOS 15. If a container needs multiple networks, specify them as additional `--network` flags.

## SSH agent forwarding

```bash
container run --ssh myimage   # mounts SSH_AUTH_SOCK into container
```

Automatically updates socket path after macOS logout/login. Useful for cloning private Git repos inside containers.

## Known DNS bugs (as of Aug 2026)

| Issue | Bug | Symptom |
|-------|-----|---------|
| Local dnsmasq conflict | #402 | DNS fails when something binds port 53 on specific interfaces |
| System DNS breakage | #1241 | Using system DNS can randomly break all egress |
| Clean install failure | #856, #1693 | Internal DNS sometimes doesn't work on fresh installs |
| UDP silent failure | #696 | UDP DNS queries silently fail; TCP works |

If DNS fails, check these first before assuming configuration error.

> Key: Embedded DNS = `sudo container system dns create <domain>` + `--name <container>` → resolves as `<name>.<domain>`. Container-to-container networking requires macOS 26. Port forward with `-p host:container`. iCloud Private Relay disabled when localhost domain is created.
