# GitOps & ArgoCD Reference

## GitOps Principles

- Git = single source of truth for cluster state
- Pull-based: controller inside cluster pulls from Git — CI never runs `kubectl apply`
- Declarative: desired state lives in Git, controller reconciles actual → desired
- Audit trail free: every change = Git commit with author, timestamp, diff
- Drift detection: controller compares live state vs Git, flags divergence
- Rollback = `git revert` — no imperative undo commands

## Why NOT kubectl apply from CI

| Problem | Detail |
|---|---|
| Network exposure | K8s API exposed to external CI runner network |
| Config drift | Cluster state diverges from repo after manual edits |
| No reconciliation | One-shot apply, no continuous correction |
| Security risk | CI runner needs cluster-admin creds — leaked token = full access |
| No rollback | Must re-run pipeline; no declarative "desired state" to restore |

## ArgoCD Architecture

- Runs inside K8s cluster (not external)
- Monitors Git repo for manifest changes (polling or webhook)
- Syncs cluster state to match Git automatically or on approval
- Supports: Helm, Kustomize, plain YAML, Jsonnet
- Components: API Server, Repo Server, Application Controller, Redis (cache)

```
Git Repo ──webhook──▶ ArgoCD Controller ──reconcile──▶ K8s Cluster
                         │
                    compare live vs desired
                         │
                    sync if drifted
```

## Sync Waves (Topological Ordering)

Annotation controls deploy order:

```yaml
argocd.argoproj.io/sync-wave: "N"   # string integer, default "0"
```

Deploy order (ascending wave number):

| Wave | Resources |
|---|---|
| `-5` | ConfigMaps, Secrets, PVCs, RBAC |
| `0` | Databases, caches (StatefulSets) |
| `1` | Backend APIs (Deployments) |
| `2` | Frontend gateways, Ingress |

Within same wave: ordered by **phase → kind → name**.

> [!IMPORTANT]
> Wave value must be string, not integer: `"1"` not `1`.

## Resource Hooks

Annotation triggers Jobs/Pods at specific sync phases:

```yaml
argocd.argoproj.io/hook: <Phase>
```

**Phases:**

| Phase | When |
|---|---|
| `PreSync` | Before main sync (DB migrations, smoke checks) |
| `Sync` | During main sync |
| `PostSync` | After all resources synced (notifications, integration tests) |
| `SyncFail` | On sync failure (alerting, rollback triggers) |
| `PostDelete` | After application deleted (cleanup) |

**Delete policies** (`argocd.argoproj.io/hook-delete-policy`):

| Policy | Behavior |
|---|---|
| `BeforeHookCreation` | Delete old hook before creating new (default) |
| `HookSucceeded` | Delete after success |
| `HookFailed` | Delete after failure |
| Combine | `HookSucceeded,HookFailed` — always clean up |

## DB Migration via PreSync Hook

Run schema migration before app deploys. Job must succeed or sync aborts.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: liquibase-schema-migration
  namespace: production
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
    argocd.argoproj.io/sync-wave: "-5"
spec:
  template:
    spec:
      containers:
      - name: liquibase-migrator
        image: liquibase/liquibase:latest
        command:
          - liquibase
          - --changeLogFile=db/changelog/db.changelog-master.yaml
          - --url=jdbc:postgresql://postgres-cluster:5432/app_db
          - --username=$(DB_USER)
          - --password=$(DB_PASSWORD)
          - update
        envFrom:
          - secretRef:
              name: database-credentials
      restartPolicy: Never
  backoffLimit: 3
  activeDeadlineSeconds: 300
```

Key points:
- `PreSync` + wave `-5` = runs first, before any app resources
- `BeforeHookCreation` = old Job deleted before new one created (avoids name collision)
- `backoffLimit: 3` = retry up to 3 times on failure
- `activeDeadlineSeconds: 300` = hard timeout, prevents stuck migrations
- Migration failure → sync aborts → app stays on previous version

## Kustomize Image Update

CI pipeline final step: update image tag in infra repo. ArgoCD handles deploy.

```bash
# CI pipeline (e.g., GitHub Actions) — after build+push image
cd infra-repo/overlays/production
kustomize edit set image myapp=registry.com/myapp:${GIT_SHA}
git add . && git commit -m "deploy: myapp ${GIT_SHA}" && git push
```

Flow:
```
App Repo CI ──build+push image──▶ Registry
     │
     └──update tag──▶ Infra Repo ──detected──▶ ArgoCD ──sync──▶ Cluster
```

> [!TIP]
> Use Git SHA as tag, not `latest`. Immutable tags = reproducible deploys.

## Best Practices

| Practice | Rationale |
|---|---|
| Separate infra repo from app repo | Minimize blast radius; independent deploy cadence |
| External Secrets Operator or Sealed Secrets | No plaintext creds in Git |
| Helm sub-charts for dependency ordering | Enforce deploy topology beyond sync waves |
| `IgnoreExtraneous` for generated resources | `argocd.argoproj.io/compare-options: IgnoreExtraneous` — skip generated CRDs |
| Health checks on all resources | ArgoCD waits for healthy before next wave |
| Webhook + polling fallback | Webhook for speed, polling (3min default) as safety net |
| RBAC per Application | Namespace-scoped AppProjects, not cluster-wide |
| Auto-sync with self-heal | `syncPolicy.automated.selfHeal: true` — revert manual cluster edits |
| Prune orphaned resources | `syncPolicy.automated.prune: true` — delete resources removed from Git |

## Anti-Patterns

- ❌ `kubectl apply` from CI pipeline — defeats GitOps model
- ❌ Storing secrets in plaintext in Git repo
- ❌ Using `latest` tag — non-deterministic deploys
- ❌ Single monorepo for app + infra — noisy diffs, accidental syncs
- ❌ Manual cluster edits without Git commit — creates drift
- ❌ Skipping health checks — next wave deploys against broken dependencies
