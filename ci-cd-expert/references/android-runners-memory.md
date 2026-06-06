# Runners & Memory Optimization

## Runner Comparison (2026)

| Runner | Hardware | Platform Fee (Private) | Notes |
|--------|----------|----------------------|-------|
| GitHub-hosted Linux | 2-vCPU, 7GB RAM, 3GB swap | Free tier minutes | Supports nested KVM |
| Physical self-hosted | Bare-metal Apple Silicon/Intel | $0.002/min | High mgmt overhead |
| Third-party cloud (WarpBuild/Depot/Namespace) | AMD64/ARM64 bare-metal VMs | $0.002/min | 2× speed, ½ price vs GitHub-hosted; low mgmt |

Self-hosted concurrency: max 4 parallel runs per M2/M3 Pro — prevents CPU starvation + disk I/O bottleneck.

## Memory Expansion (Standard Free Runners)

Default 7GB RAM + 3GB swap insufficient for R8 shrinking, multi-module Kotlin compile, heavy resource linking → OOM.

Fix: reclaim ~10GB disk → replace 3GB swap with 10GB → 17GB virtual memory → safe `org.gradle.jvmargs=-Xmx6g`.

```yaml
- name: Optimize Runner Memory and Disk Space
  run: |
    sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /usr/share/swift
    sudo swapoff -a
    sudo rm -f /mnt/swapfile
    sudo dd if=/dev/zero of=/mnt/swapfile bs=1M count=10240
    sudo chmod 600 /mnt/swapfile
    sudo mkswap /mnt/swapfile
    sudo swapon /mnt/swapfile
```

Run **early** in workflow — before any compile task.
