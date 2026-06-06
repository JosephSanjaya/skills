---
name: ci-cd-expert
description: |
  Enterprise CI/CD, optimization, security, & delivery expert. Covers GHA, GitLab CI, Jenkins, monorepos (Turbo, Nx, Bazel), containers (BuildKit, Kaniko), GitOps (Argo), delivery (Spinnaker, Kayenta, Fastlane, Flyway), OIDC, and Android.
  Use for: pipelines, caching, GitOps, monorepos, OIDC, DB migrations, mobile DevOps, or debugging.
  Triggers: CI/CD, pipeline, workflow, deployment, GitHub Actions, GitLab CI, Jenkins, ArgoCD, GitOps, Kaniko, Docker build, canary, Spinnaker, Kayenta, Fastlane, OIDC, monorepo CI, Bazel, cache strategy, DAG pipeline, reusable workflow, composite action, sync waves, zero-downtime migration, PPE, code signing, android CI, gradle cache CI, optimize android build, affected modules, keystore signing, pre-push hook android, android emulator CI, KVM CI, swap runner memory, roborazzi CI, nektos/act android, cancel in progress workflow.
---

# CI/CD Expert

<instructions>

## Quick Decision Tree

```
What need?
├── Platform selection → references/platforms.md
├── GitHub Actions architecture → references/github-actions.md
├── GitLab CI optimization → references/gitlab-ci.md
├── Monorepo pipeline (JS/TS) → references/monorepo-frontend.md
├── Monorepo pipeline (compiled) → references/monorepo-bazel.md
├── Container builds (K8s) → references/container-builds.md
├── GitOps + ArgoCD deploy → references/gitops-argocd.md
├── DB migrations in pipeline → references/db-migrations.md
├── Canary / progressive delivery → references/progressive-delivery.md
├── Mobile CI/CD (iOS/Android) → references/mobile-devops.md
├── Android affected modules & testing → references/android-affected-testing.md
├── Android signing & release → references/android-signing-release.md
├── Android Gradle tuning & caching → references/android-gradle-tuning.md
├── Android pre-merge & emulator → references/android-emulator-validation.md
├── Android runner memory & swap → references/android-runners-memory.md
├── Pipeline security (OIDC/PPE) → references/security-oidc.md
└── Full config samples → references/samples.md
```

## Core Principles

1. **DAG > Sequential.** Never chain jobs linearly. Use `needs` (GitLab) or job dependencies (GHA) for parallel fan-out/fan-in.
2. **Cache everything.** Hash lock files for cache keys. Use fallback keys. Distribute cache via S3/NFS at scale.
3. **Impact radius only.** Never rebuild world. Use affected/changed detection (Nx, Turborepo, Bazel, dropbox/affectedmoduledetector, `git diff`).
4. **Immutable tags.** Use Git SHA tags (`v1.2.3-a3f5b2c`), never `latest`. Pin 3rd-party actions to commit SHAs.
5. **Zero static secrets.** OIDC federation for cloud access. Short-lived JWT tokens. No long-lived IAM keys.
6. **GitOps pull > CI push.** ArgoCD/Flux pull from Git. Never `kubectl apply` from CI runner.
7. **Fail fast.** Lint/syntax first. `interruptible: true` on superseded commits. Kill redundant jobs.
8. **Build once, promote.** Single artifact through all environments. No per-env rebuilds.

## Platform Selection Cheat Sheet

| Platform | Best For | Avoid When |
|----------|----------|------------|
| **GitHub Actions** | Teams <50, OSS, rapid setup | Need self-hosted control, complex loops |
| **GitLab CI/CD** | Enterprise compliance, self-hosted, DAGs | Already deep in GitHub ecosystem |
| **Jenkins** | Legacy integration, multi-VCS, extreme flex | Greenfield projects (maintenance overhead) |
| **CircleCI** | Startups needing raw speed | Need native SCM integration |
| **Bazel** | Polyglot monorepo >1M LOC, hermetic builds | Small projects (setup overhead) |

## GitHub Actions: Reusable Workflows vs Composite Actions

| | Reusable Workflows | Composite Actions |
|-|-------------------|-------------------|
| **Level** | Job-level orchestration | Step-level encapsulation |
| **Jobs** | Multiple jobs, own `runs-on` | No jobs, runs on caller's runner |
| **Secrets** | Native `secrets:` passing | Must pass via env vars |
| **Logging** | Per-step visibility | Single collapsed step |
| **Matrix** | Own `strategy.matrix` | None (caller controls) |

**Rule:** Workflows = pipeline templates. Actions = task templates. Never mix.

## GitLab CI: DAG + Dynamic Pipelines

```yaml
# Fan-out with needs (bypass stage waits)
test-unit:
  stage: test
  needs: [build]
  script: make test-unit

test-integration:
  stage: test
  needs: [build]
  script: make test-integration

deploy:
  stage: deploy
  needs: [test-unit, test-integration]  # fan-in
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  interruptible: false
```

Dynamic parent-child for monorepos:
```yaml
generate-config:
  stage: setup
  script: python generate_pipeline.py --base origin/main --output child.yml
  artifacts:
    paths: [child.yml]

trigger-child:
  stage: trigger
  needs: [generate-config]
  trigger:
    include:
      - artifact: child.yml
    strategy: depend
```

## Caching Strategy

| Platform | Cache Key Pattern | Fallback |
|----------|------------------|----------|
| **GHA** | `${{ runner.os }}-node-${{ hashFiles('**/pnpm-lock.yaml') }}` | `${{ runner.os }}-node-` |
| **GitLab** | `cache:key:files: [yarn.lock]` | Default branch cache |
| **Turborepo** | `globalDependencies` + `outputs` arrays | Remote cache (Vercel) |
| **Nx** | `namedInputs` + `inputs` per target | Nx Cloud remote cache |
| **Bazel** | `--disk_cache` + `--remote_cache` | N/A (hermetic) |

## Container Build Decision

```
Need privileged access?
├── YES (trusted runners) → Docker BuildKit (fast, local cache)
└── NO (shared K8s, multi-tenant)
    └── Kaniko (daemonless, userspace, --cache=true --cache-repo=...)
```

Always use multi-stage Dockerfiles: heavy builder → minimal runtime (`scratch`/`alpine`).

## GitOps Flow

```
CI Pipeline                          K8s Cluster
┌──────────┐    commit SHA tag    ┌────────────┐
│ Build +  │ ──→ Update manifest  │  ArgoCD /  │
│ Test     │     in infra repo    │  Flux      │
│ └──────────┘    (Kustomize edit)  │  (pull)    │
│                                   └────────────┘
```

ArgoCD Sync Wave order: Wave -5 (secrets/PVCs) → Wave 0 (DB) → Wave 1 (backend) → Wave 2 (frontend).

## Zero-Downtime DB Migration

```
Phase 1: EXPAND    → ALTER TABLE ADD COLUMN (additive only)
Phase 2: DUAL-WRITE → App writes both old + new columns
Phase 3: BACKFILL  → Background worker migrates legacy data
Phase 4: CONTRACT  → DROP old column (days later, after telemetry confirms)
```

Execute via ArgoCD `PreSync` hooks with `backoffLimit: 3` + `activeDeadlineSeconds: 300`.

## OIDC Federation (Zero Static Secrets)

```
CI Job starts → Platform generates JWT (aud + sub claims)
  → Cloud provider validates JWT signature
  → Evaluates sub claim against IAM trust policy
  → Returns short-lived STS credentials
  → Credentials auto-expire post-job
```

Lock sub claim to exact repo + branch: `repo:org/repo:ref:refs/heads/main`.

## Reference Files

| File | Read When |
|------|-----------|
| [platforms.md](references/platforms.md) | Comparing/selecting CI/CD platforms |
| [github-actions.md](references/github-actions.md) | Writing GHA workflows, reusable workflows, composite actions |
| [gitlab-ci.md](references/gitlab-ci.md) | GitLab DAGs, rules, dynamic pipelines, caching |
| [monorepo-frontend.md](references/monorepo-frontend.md) | Turborepo/Nx config, affected logic, cache tuning |
| [monorepo-bazel.md](references/monorepo-bazel.md) | Bazel setup, presubmit.yml, remote exec, Gazelle |
| [container-builds.md](references/container-builds.md) | Kaniko vs BuildKit, multi-stage, K8s pod specs |
| [gitops-argocd.md](references/gitops-argocd.md) | ArgoCD sync waves, hooks, Kustomize, Helm |
| [db-migrations.md](references/db-migrations.md) | Expand-Contract, Flyway/Liquibase, PreSync hooks |
| [progressive-delivery.md](references/progressive-delivery.md) | Canary, Spinnaker, Kayenta config, statistical analysis |
| [mobile-devops.md](references/mobile-devops.md) | Fastlane Match, Fastfile, iOS/Android signing |
| [android-affected-testing.md](references/android-affected-testing.md) | Android affected module detection, test-only modules, Roborazzi |
| [android-signing-release.md](references/android-signing-release.md) | Android GHA keystore signing, GPG/base64, Play Store upload |
| [android-gradle-tuning.md](references/android-gradle-tuning.md) | Android compiler tuning (KSP), configuration/remote cache |
| [android-emulator-validation.md](references/android-emulator-validation.md) | Android git hooks auto-install, act dry-run, KVM emulator permissions |
| [android-runners-memory.md](references/android-runners-memory.md) | Android runner comparison, swap space expansion (17GB RAM) |
| [security-oidc.md](references/security-oidc.md) | OIDC federation, PPE prevention, trust policies |
| [samples.md](references/samples.md) | Full working config samples for all platforms |
| [hyperscale.md](references/hyperscale.md) | Stripe STE, Uber/Airbnb Bazel, Netflix Spinnaker |

</instructions>

<constraints>
- Pin 3rd-party actions to full commit SHAs, never mutable tags.
- Enforce OIDC (zero static secrets) for all cloud deployments.
- Build containers using multi-stage Dockerfiles. Use Kaniko in shared/restricted Kubernetes, BuildKit in isolated runners.
- DB migrations must run in PreSync hook / wave -5 using additive-only SQL first (Expand-and-Contract).
- Enable `interruptible: true` in GitLab and `cancel-in-progress` in GHA to kill redundant runs.
- Run swap space expansion early on standard free GitHub Actions runners to reclaim space and enable safe `-Xmx6g` Gradle heap.
- Always configure Gradle cache encryption via `cache-encryption-key` and restrict cache write access (`cache-read-only`) to production/release branches.
- Run UI/screenshot checks (e.g. Roborazzi) and instrumentation tests on a nightly schedule or triggered on UI directory changes to avoid slowing down developer PR loops.
- Auto-install local Git hooks (e.g. pre-push) by registering an `installLocalGitHooks` copy task in the root Gradle build configuration.
</constraints>
