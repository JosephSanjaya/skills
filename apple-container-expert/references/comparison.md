# Comparison with Alternatives

## Performance benchmarks

Sources: zot24/macos-container-benchmarks (M3, macOS 26.4, v0.11.0); astgl.com/James Cruce (M3 Ultra, v1.x). Benchmarks pre-date v1.2.2 — numbers may shift, architectural tradeoffs unchanged.

| Metric | Apple container | Docker Desktop | OrbStack | Colima |
|--------|----------------|----------------|----------|--------|
| Container cold start | ~1,071 ms | ~360 ms | ~371 ms | ~291 ms |
| Postgres accepting connections (cold) | ~2,081 ms | ~292 ms | — | — |
| Bind-mount write | ~32.6 MB/s | ~96.7 MB/s | ~548.5 MB/s | — |
| Named volume write | ~1,280 MB/s | — | — | — |
| Named volume read | — | — | ~10,061 MB/s | — |
| Container-to-container throughput | ~23 Gbps | ~130 Gbps | ~110 Gbps | — |
| Spin up 40 containers | ~35 s | ~9 s | ~9 s | — |
| **Idle RAM footprint** | **~51 MB** | ~1,124 MB | ~1,631 MB | ~200 MB |

The idle RAM win scales linearly: at 10 running containers, Docker Desktop uses ~11 GB idle vs. apple/container's ~510 MB. This is the single largest advantage for memory-constrained workflows.

## Feature matrix

| Feature | Apple container | Docker Desktop | OrbStack | Colima |
|---------|----------------|----------------|----------|--------|
| Price | Free (Apache-2.0) | Free (< 250 emp / $10M rev) | ~$8–10/seat/mo | Free |
| Platform | Apple Silicon macOS only | Cross-platform | Mac only | Mac/Linux |
| Docker Compose | No | Yes | Yes | Yes (Docker API) |
| GPU / Metal | No | No (macOS) | No (macOS) | No |
| Rosetta x86_64 | Yes — native, fast (~80% speed) | Via QEMU (slow) | Transparent | Via QEMU |
| Isolation | Hypervisor VM per container | cgroups in shared VM | cgroups in shared VM | cgroups in shared VM |
| `container machine` (WSL-like) | Yes | No | No | No |
| Idle RAM | ~51 MB (22–32× less than rivals) | ~1,124 MB | ~1,631 MB | ~200 MB |
| DevContainers | Partial (gaps) | Full | Full | Full |
| Intel Mac support | No | Yes | No | Yes |

## Use-case guidance

### Use apple/container when

- **Single-service dev**: databases, caches, web servers, message brokers — run one service at a time
- **Memory-sensitive**: running heavy native workloads (ML, Xcode) alongside containers; ~51 MB idle is exceptional
- **Security / agent sandboxing**: hypervisor boundary (not just cgroups) for untrusted or AI-generated code
- **Free with no licensing concerns**: Apache-2.0, no employee/revenue thresholds
- **Long-running datastores**: community benchmark found apple/container faster than Colima for sustained Redis/Postgres/ClickHouse workloads
- **WSL-like Linux env**: `container machine` with home directory mounting

### Stay on OrbStack when

- Fastest bind-mount file I/O (hot-reload, `node_modules`, webpack, Vite)
- Docker Compose / multi-service YAML orchestration
- Best all-around polish with Docker API compatibility

### Stay on Docker Desktop when

- Cross-platform team (not Mac-only)
- Full Docker ecosystem: Scout, Extensions, GUI, Buildx
- Compose-heavy workflows, existing muscle memory

### Stay on Colima when

- Free + Docker API compatibility needed
- Fastest raw short-lived container starts (~291 ms)
- Minimal footprint without commercial licensing concerns

## Verdict (Aug 2026)

| | apple/container | Competition |
|--|-----------------|-------------|
| Isolation security | Hypervisor VM (best) | cgroups in shared VM |
| Idle RAM | ~51 MB (22–32× less) | 1,124–1,631 MB |
| Cold start | ~1,071 ms (3× slower than Colima) | 291–371 ms |
| Bind-mount I/O | ~32.6 MB/s (17× slower than OrbStack) | up to 548 MB/s |
| Docker Compose | No | Yes (all alternatives) |
| GPU/Metal | No | No (macOS limitation for all) |

**Use apple/container**: single-service dev, idle-RAM-sensitive (ML coexistence), security sandboxing, free Apache-2.0.
**Stay on OrbStack**: Compose, hot-reload, bind-mount-heavy, polished GUI.
**Stay on Colima**: free + Docker API + fastest cold starts.
