# Container Build Architectures

## Decision Tree

```
Build containers in K8s?
├── Trusted, isolated runners → Docker BuildKit (fast, local cache)
└── Shared K8s, multi-tenant, zero-trust → Kaniko (daemonless, userspace)
```

## Docker BuildKit vs Kaniko

| Feature | Docker BuildKit | Kaniko |
|---------|----------------|--------|
| Architecture | Daemon-reliant (DinD sidecar or socket mount) | Daemonless, userspace execution |
| Speed | Fast: local layer cache, parallel stage exec | Slower: remote registry round-trips for cache |
| Security | **DANGEROUS**: `--privileged` or host socket = full kernel access | Safe: no privileged access, no daemon |
| Multi-platform | Native multi-platform manifests (`linux/amd64`, `linux/arm64`) | Not natively supported |
| SSH/secrets | SSH forwarding, secret mounts | N/A |
| Use when | Isolated, dedicated, trusted CI runners | Shared K8s clusters, regulated environments |

## Kaniko K8s Pod Spec

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kaniko-builder
  namespace: ci-cd-runners
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    args:
      - "--dockerfile=/workspace/Dockerfile"
      - "--context=dir://workspace"
      - "--destination=registry.example.com/app:v2.4.1"
      - "--cache=true"
      - "--cache-repo=registry.example.com/kaniko-cache"
      - "--cache-ttl=168h"
      - "--compressed-caching=false"
    volumeMounts:
      - name: workspace-volume
        mountPath: /workspace
      - name: kaniko-secret
        mountPath: /kaniko/.docker
    resources:
      requests:
        cpu: 1000m
        memory: 2Gi
  restartPolicy: Never
  volumes:
    - name: workspace-volume
      persistentVolumeClaim:
        claimName: source-code-pvc
    - name: kaniko-secret
      secret:
        secretName: docker-registry-credentials
        items:
        - key: .dockerconfigjson
          path: config.json
```

## Key Kaniko Flags

| Flag | Purpose |
|------|---------|
| `--cache=true` | Enable layer caching |
| `--cache-repo=REPO` | Remote registry for cached layers |
| `--cache-ttl=168h` | Cache time-to-live (7 days) |
| `--compressed-caching=false` | Faster at cost of storage (skip compression) |
| `--dockerfile=PATH` | Dockerfile location within context |
| `--context=dir://PATH` | Build context source |
| `--destination=REPO:TAG` | Push target (use Git SHA tags) |

## Registry Auth

Mount K8s Secret containing `.dockerconfigjson` to `/kaniko/.docker/config.json`.

```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=USER \
  --docker-password=PASS
```

## Multi-Stage Dockerfile

```dockerfile
# Stage 1: Heavy builder
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download          # Cache deps layer
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server ./cmd/server

# Stage 2: Minimal runtime
FROM scratch
COPY --from=builder /app/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/server"]
```

## Layer Ordering Rules

1. Copy dependency manifests first (`go.mod`, `package.json`)
2. Install dependencies (cached if manifest unchanged)
3. Copy source code last (changes most frequently)
4. Use `.dockerignore` to exclude `.git`, `node_modules`, test files

## Anti-Patterns

| Anti-Pattern | Why Bad | Fix |
|-------------|---------|-----|
| `latest` tag | Non-deterministic deploys | Git SHA tags (`v1.2.3-a3f5b2c`) |
| Single-stage build | Bloated image with dev tooling | Multi-stage: builder → scratch/alpine |
| DinD in shared K8s | Full kernel access, container escape | Kaniko (userspace) |
| No Kaniko cache | Full rebuild every time | `--cache=true --cache-repo=...` |
| Early `COPY . .` | Busts cache on any source change | Copy manifests first, then source |
| Running as root | Security risk in runtime | `USER nonroot` in final stage |
