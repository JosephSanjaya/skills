# Architecture

## Process model

`container system start` → launchd registers `container-apiserver` → spawns XPC helpers:

| Process | Role |
|---------|------|
| `container-apiserver` | Central coordinator, client-facing API over XPC; managed by launchd |
| `container-core-images` | OCI image lifecycle, layer extraction, content store, registry sync |
| `container-network-vmnet` | Virtual bridge, vmnet interface allocation, IP assignment, routing |
| `container-runtime-linux` | One instance per container; manages guest VM lifecycle and comms |

Inside each micro-VM: **`vminitd`** — minimal Swift static binary (musl), communicates with `container-runtime-linux` over virtio-vsock/gRPC. Handles: process launch, stdio stream multiplexing, signal propagation (SIGTERM/SIGKILL), execution state reporting. No runc/containerd inside the guest — this is why boot is sub-second.

## VM backends

| Backend | Platform | Hypervisor |
|---------|----------|------------|
| `VZVirtualMachineManager` | macOS (default production path) | Apple Virtualization.framework; no external hypervisor binaries |
| `CHVirtualMachineManager` | Linux CI/CD | cloud-hypervisor + KVM (`/dev/kvm`); UDS REST API; virtio-blk storage; virtiofsd over virtio-fs |

The `Containerization` Swift package abstracts both backends behind `VirtualMachineManager` / `VirtualMachineInstance` protocols.

## macOS 15 vs macOS 26

| Feature | macOS 26 | macOS 15 |
|---------|----------|----------|
| Container-to-container networking | Full vmnet bridge routing | Blocked — strictly isolated |
| `container network create` | Supported | Fatal error |
| Subnet stability | Dynamic XPC + vmnet sync | Race condition → IP disagreement → total network drop |
| Maintenance | Primary target, full support | Unmaintained — bugs not fixed if unreproducible on macOS 26 |

## Core design difference vs Docker/OrbStack/Colima

Every container boots its **own Linux kernel** in a hardware-enforced VM (Virtualization.framework). Docker Desktop/OrbStack/Colima share a single VM with all containers inside it via cgroups/namespaces. Benefits: hypervisor-level isolation, dedicated IP per container, per-container host path scoping. Costs: higher per-container overhead (~1,071 ms cold start vs ~360 ms for Docker).

## Why boot is fast despite a full VM

- Minimal guest rootfs (only core utilities)
- vminitd communicates via virtio-vsock/gRPC — no systemd/openrc overhead
- Virtualization.framework native integration; no QEMU layer
- Apple quotes "a few hundred milliseconds"; community benchmarks measure ~1 s on M3 Ultra

> Key: One VM per container (not shared). XPC helpers: apiserver → core-images + network-vmnet + one runtime-linux per container. macOS 26 required for full networking features.
