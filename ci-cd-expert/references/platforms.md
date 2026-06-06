# CI/CD Platform Selection Guide

## Platform Profiles

### GitHub Actions
- **Paradigm:** Cloud-native, GitHub SaaS-coupled
- **Strengths:** Native repo integration, serverless scaling, 20k+ marketplace actions, YAML simplicity, zero-to-production in hours, free tier generous for OSS
- **Weaknesses:** Vendor lock-in to GitHub, limited self-hosted runner control, SSH debugging painful (`tmate` workaround), no native loops/functions in YAML, matrix strategy is closest substitute
- **Ideal for:** Teams <50 devs, OSS projects, rapid CI/CD bootstrap

```yaml
# Minimal GHA — build + test in ~15 lines
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm test
```

### GitLab CI/CD
- **Paradigm:** Unified DevOps platform (SCM + CI + CD + Security + Registry)
- **Strengths:** Built-in SAST/DAST/dependency scanning, unified repo+pipeline+registry, DAG pipeline scheduling, container registry included, compliance frameworks built-in, merge train support
- **Weaknesses:** Platform complexity high, steep learning curve, best value inside GitLab ecosystem only, self-hosted resource-hungry (8GB+ RAM minimum)
- **Ideal for:** Enterprises needing compliance/audit trails, self-hosted requirements, regulated industries

```yaml
# GitLab CI — DAG pipeline
stages: [build, test, deploy]
build:
  stage: build
  script: make build
  artifacts:
    paths: [dist/]
test:
  stage: test
  needs: [build]   # DAG — skip waiting for unrelated jobs
  script: make test
```

### Jenkins
- **Paradigm:** Open-source automation server, self-hosted
- **Strengths:** Infinite flexibility, 1800+ plugins, hardware-agnostic, any VCS supported, Groovy/declarative/scripted pipelines, battle-tested 15+ years
- **Weaknesses:** High maintenance burden, dedicated infra team needed, Groovy scripting complexity, needs 5-10 external tool integrations (SonarQube, Artifactory, etc.), security patching constant, UI dated
- **Ideal for:** Legacy system integration, multi-VCS environments, extreme infrastructure constraints, air-gapped networks

```groovy
// Declarative Jenkinsfile
pipeline {
  agent any
  stages {
    stage('Build') { steps { sh 'make build' } }
    stage('Test')  { steps { sh 'make test' } }
  }
}
```

### CircleCI
- **Paradigm:** Cloud-native execution engine
- **Strengths:** Raw build performance fast, rapid autoscaling, optimized layer caching, orbs (reusable config packages), resource classes for CPU/RAM tuning, test splitting built-in
- **Weaknesses:** Webhook-based integration (not native SCM), isolated from source platform, pricing spikes at scale, config complexity grows fast
- **Ideal for:** Startups needing speed, performance-critical pipelines, teams optimizing build minutes

```yaml
# CircleCI — orb usage
version: 2.1
orbs:
  node: circleci/node@5.0
workflows:
  build:
    jobs:
      - node/test
```

### Bamboo
- **Paradigm:** Atlassian ecosystem CI/CD
- **Strengths:** Deep Jira/Bitbucket/Confluence integration, deployment project tracking, built-in agent management
- **Weaknesses:** Eclipsed by competitors, slow feature cadence, Atlassian shifting focus to Bitbucket Pipelines, limited community, commercial-only
- **Ideal for:** Teams already deep in Atlassian stack (Jira + Bitbucket + Confluence)

> [!WARNING]
> Atlassian announced Bamboo end-of-life plans. Evaluate migration path before new adoption.

### Harness CI
- **Paradigm:** AI-powered CI/CD platform
- **Strengths:** Automated migration from other platforms, stage-level parallelism, SLSA L3 supply chain compliance, test intelligence (skip unchanged tests), built-in governance/policy engine
- **Weaknesses:** Commercial licensing required, newer ecosystem (smaller community), fewer integrations than mature platforms
- **Ideal for:** Enterprises prioritizing supply chain security, teams migrating from Jenkins at scale

---

## Decision Matrix

| Criteria | GitHub Actions | GitLab CI | Jenkins | CircleCI | Bamboo | Harness CI |
|---|---|---|---|---|---|---|
| **Setup Speed** | ⚡ Hours | 🕐 Days | 🕐 Days-Weeks | ⚡ Hours | 🕐 Days | 🕐 Days |
| **Maintenance** | None (SaaS) | Medium-High | Very High | None (SaaS) | Medium | Low (SaaS) |
| **Flexibility** | Medium | High | Unlimited | Medium | Low | High |
| **Security Built-in** | Basic | Excellent | Plugin-dependent | Basic | Basic | Excellent |
| **Self-hosted** | Partial (runners) | Full | Full | Partial (runners) | Full | Partial |
| **SCM Coupling** | GitHub only | GitLab only | Any VCS | Any (webhook) | Bitbucket | Any |
| **Scaling** | Auto (SaaS) | Manual/Auto | Manual | Auto (SaaS) | Manual | Auto (SaaS) |
| **Learning Curve** | Low | Medium-High | High | Medium | Medium | Medium |
| **OSS Friendly** | Excellent | Good | Excellent | Limited | No | No |
| **Compliance/Audit** | Basic | Excellent | Plugin-dependent | Basic | Basic | Excellent |
| **Team Size Sweet Spot** | 1-50 | 50-500+ | Any | 5-100 | 10-200 | 50-500+ |

### Quick Decision Flow

```
Need compliance/audit? → GitLab CI or Harness CI
Already on GitHub? → GitHub Actions
Multi-VCS or air-gapped? → Jenkins
Need fastest builds? → CircleCI
Deep Atlassian stack? → Bamboo (but plan migration)
Supply chain security priority? → Harness CI
Budget = $0? → GitHub Actions (OSS) or Jenkins
```

---

## Migration Considerations

### Before Migration
- **Audit current state:** Count pipelines, secrets, custom scripts, plugin dependencies
- **Map abstractions:** Each platform names things differently — jobs/stages/steps/tasks
- **Identify blockers:** Custom plugins, proprietary integrations, compliance requirements

### Terminology Mapping

| Concept | GitHub Actions | GitLab CI | Jenkins | CircleCI |
|---|---|---|---|---|
| Pipeline file | `.github/workflows/*.yml` | `.gitlab-ci.yml` | `Jenkinsfile` | `.circleci/config.yml` |
| Execution unit | Job | Job | Stage | Job |
| Grouping | Workflow | Pipeline | Pipeline | Workflow |
| Reusable config | Composite Action | Include/Extend | Shared Library | Orb |
| Secrets | Repository/Org Secrets | CI/CD Variables | Credentials Store | Context/Env Vars |
| Caching | `actions/cache` | `cache:` keyword | Plugin-dependent | `save_cache/restore_cache` |
| Artifacts | `actions/upload-artifact` | `artifacts:` keyword | `archiveArtifacts` | `store_artifacts` |

### Migration Anti-Patterns
- ❌ Lift-and-shift without restructuring — each platform has different strengths
- ❌ Migrating secrets manually — use vault/secrets manager as intermediary
- ❌ Big-bang migration — migrate non-critical pipelines first, validate, then move critical ones
- ❌ Ignoring runner/executor differences — test on target platform runners early
- ❌ Keeping platform-specific hacks — clean up during migration, not after

### Migration Order (recommended)
1. Lint/format pipelines (low risk, fast feedback)
2. Unit test pipelines
3. Build/package pipelines
4. Integration test pipelines
5. Deployment pipelines (highest risk — migrate last)

---

## Cost Comparison Tips

### Pricing Models

| Platform | Model | Free Tier | Key Cost Driver |
|---|---|---|---|
| GitHub Actions | Per-minute | 2000 min/mo (free), 3000 min/mo (Pro) | Minutes × runner multiplier (Linux=1x, macOS=10x, Windows=2x) |
| GitLab CI | Per-minute (SaaS) or self-hosted | 400 min/mo (free) | Compute minutes, storage, transfer |
| Jenkins | Self-hosted only | Free (OSS) | Infra + ops team salary (hidden cost huge) |
| CircleCI | Per-credit | 6000 credits/mo | Credits × resource class size |
| Bamboo | Per-agent license | None | Agent count × license fee |
| Harness CI | Per-developer | Limited free | Developer seat count |

### Cost Gotchas
- **GitHub Actions:** macOS runners 10x Linux cost — use Linux where possible, macOS only for iOS/Swift builds
- **GitLab CI:** Self-hosted saves SaaS minutes but adds infra cost — break-even usually ~20 developers
- **Jenkins:** "Free" misleading — typical Jenkins infra costs $50-200k/yr including ops engineer time
- **CircleCI:** Resource class upgrades compound fast — `xlarge` = 8x `medium` cost per minute
- **All platforms:** Cache misses = wasted minutes — invest in caching strategy early

### Cost Optimization Patterns
- Use path filters — skip pipelines when irrelevant files change
- Parallelize tests — more concurrent jobs = shorter wall time (but same total minutes)
- Cache aggressively — dependency caches, Docker layer caches, build caches
- Use spot/preemptible runners where available (GitLab, self-hosted GHA)
- Right-size runners — don't use `xlarge` for linting
- Schedule expensive jobs (integration tests, security scans) — run nightly not per-push
- Implement affected-module detection — build/test only changed modules in monorepos
