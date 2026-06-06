# GitHub Actions Reference

## Reusable Workflows vs Composite Actions

### Comparison

| Aspect | Reusable Workflow | Composite Action |
|--------|------------------|-----------------|
| Scope | Job-level | Step-level |
| Runner | Own `runs-on` | Caller's runner |
| Secrets | Native `secrets:` block | Pass via `env:` vars |
| Logging | Real-time per-step | Single collapsed step |
| Matrix | Own `strategy.matrix` | None (caller controls) |
| Nesting | Max 10 levels | Max 10 levels |
| Post-call steps | Cannot append steps after call | Can add steps before/after |
| Use case | Pipeline templates, compliance | Task abstraction, Docker builds |

### Rule

Workflows = pipeline templates (compliance gates, deploy pipelines). Actions = task templates (Docker build, Terraform apply, lint+format).

### Reusable Workflow — Called Workflow

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      node-version:
        required: false
        type: string
        default: '20'
    secrets:
      DEPLOY_KEY:
        required: true
    outputs:
      deploy-url:
        description: "Deployed URL"
        value: ${{ jobs.deploy.outputs.url }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    outputs:
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - uses: actions/setup-node@2028fbc646294d13c9a0c0211130d70545f9453c # v6.0.0
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci
      - id: deploy
        run: |
          URL=$(./deploy.sh --env ${{ inputs.environment }})
          echo "url=$URL" >> "$GITHUB_OUTPUT"
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

### Reusable Workflow — Caller

```yaml
# .github/workflows/deploy-prod.yml
name: Deploy Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      node-version: '22'
    secrets:
      DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}

  # Cannot add steps inside 'deploy' job above — separate job needed
  notify:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deployed to ${{ needs.deploy.outputs.deploy-url }}"
```

### Composite Action

```yaml
# .github/actions/docker-build-push/action.yml
name: Docker Build & Push
description: Build and push Docker image with caching

inputs:
  image-name:
    required: true
    description: "Full image name"
  registry:
    required: false
    default: "ghcr.io"
  dockerfile:
    required: false
    default: "Dockerfile"

outputs:
  digest:
    description: "Image digest"
    value: ${{ steps.build.outputs.digest }}

runs:
  using: composite
  steps:
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@b5ca514318bd6ebac0fb2aedd5d36ec1b5c232a2 # v3.10.0
      shell: bash

    - name: Log in to registry
      run: echo "${{ env.REGISTRY_TOKEN }}" | docker login ${{ inputs.registry }} -u "${{ env.REGISTRY_USER }}" --password-stdin
      shell: bash

    - name: Build and push
      id: build
      uses: docker/build-push-action@263435318d21b8e681c14492fe198e19c816612b # v6.18.0
      with:
        context: .
        file: ${{ inputs.dockerfile }}
        push: true
        tags: ${{ inputs.registry }}/${{ inputs.image-name }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### Composite Action — Caller

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      # Steps before composite action
      - run: echo "Pre-build checks done"

      - uses: ./.github/actions/docker-build-push
        env:
          REGISTRY_TOKEN: ${{ secrets.GHCR_TOKEN }}
          REGISTRY_USER: ${{ github.actor }}
        with:
          image-name: myorg/myapp

      # Steps after composite action — works fine
      - run: echo "Image digest ${{ steps.build.outputs.digest }}"
```

---

## Security Best Practices

### Pin Actions to Commit SHA

Tags mutable. Attacker compromise tag → PPE (Poisoned Pipeline Execution). Pin to full SHA.

```yaml
# BAD — tag can be moved to malicious commit
- uses: actions/checkout@v6

# GOOD — immutable SHA
- uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
```

Use Dependabot or Renovate to auto-update SHA pins:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

### Environment-Scoped Secrets

Never use org-level secrets for deploy creds. Scope per environment with protection rules.

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging          # Only secrets from 'staging' environment
    steps:
      - run: ./deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}   # staging-scoped

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com
    concurrency:
      group: deploy-prod
      cancel-in-progress: false   # Never cancel running prod deploy
    steps:
      - run: ./deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}   # production-scoped, different value
```

### Avoid `secrets: inherit` in Production

`secrets: inherit` passes ALL caller secrets to called workflow. Destroys auditability — can't tell which secrets used.

```yaml
# BAD — all secrets leak to called workflow
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    secrets: inherit

# GOOD — explicit, auditable
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    secrets:
      DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      # Only what's needed, nothing more
```

### Branch-Based Testing for Shared Workflows

Test workflow changes on feature branch before merge. Use `workflow_call` + `workflow_dispatch` combo.

```yaml
# .github/workflows/reusable-ci.yml
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'
  workflow_dispatch:       # Manual trigger for testing on branch
    inputs:
      node-version:
        type: string
        default: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - uses: actions/setup-node@2028fbc646294d13c9a0c0211130d70545f9453c # v6.0.0
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci && npm test
```

Caller references branch for testing:

```yaml
# Testing on feature branch
jobs:
  ci:
    uses: myorg/shared-workflows/.github/workflows/reusable-ci.yml@feature/new-steps
    with:
      node-version: '22'

# Production — pinned to release tag (still SHA-pin in practice)
jobs:
  ci:
    uses: myorg/shared-workflows/.github/workflows/reusable-ci.yml@v2.1.0
    with:
      node-version: '20'
```

### Additional Security Patterns

```yaml
# Restrict workflow permissions — least privilege
permissions:
  contents: read
  # Only add what's needed

# Prevent script injection via untrusted input
- name: Safe input handling
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: |
    # Use env var, never interpolate directly in run:
    echo "Processing: $PR_TITLE"

# BAD — script injection risk
# run: echo "Title: ${{ github.event.pull_request.title }}"
```

---

## Matrix Strategy

### Multi-Dimensional Matrix

Test across OS × Node version × package manager simultaneously. Fast failure with `fail-fast: false` keeps other combos running.

```yaml
name: Cross-Platform CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        include:
          # Extra combo with specific flag
          - os: ubuntu-latest
            node-version: 22
            experimental: true
        exclude:
          # Skip slow/unnecessary combos
          - os: windows-latest
            node-version: 18
    continue-on-error: ${{ matrix.experimental || false }}
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - uses: actions/setup-node@2028fbc646294d13c9a0c0211130d70545f9453c # v6.0.0
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

### Matrix with Caching — 40%+ Pipeline Reduction

Combine matrix with per-combo caching. Each combo gets own cache entry.

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        node-version: [20, 22]
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - uses: actions/setup-node@2028fbc646294d13c9a0c0211130d70545f9453c # v6.0.0
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm    # Built-in cache — uses package-lock.json hash

      - run: npm ci
      - run: npm test
```

### Dynamic Matrix from JSON

Generate matrix at runtime — useful for monorepo changed-module detection.

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set.outputs.matrix }}
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - id: set
        run: |
          # Detect changed packages
          CHANGED=$(./scripts/detect-changes.sh)
          echo "matrix={\"package\":$CHANGED}" >> "$GITHUB_OUTPUT"

  test:
    needs: detect
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.detect.outputs.matrix) }}
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
      - run: npm test --workspace=${{ matrix.package }}
```

---

## Caching

### Standard Cache with Fallback Keys

Primary key = exact match. Fallback (`restore-keys`) = prefix match, stale but faster than cold.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Cache node_modules
        id: cache
        uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
        with:
          path: node_modules
          key: node-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
          restore-keys: |
            node-${{ runner.os }}-

      - if: steps.cache.outputs.cache-hit != 'true'
        run: npm ci
```

### Cache Scope

Cache scope: branch → default branch. Feature branch reads default branch cache but writes own. Default branch cache shared across all branches.

```yaml
# Gradle cache — multi-path, fallback chain
- uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
  with:
    path: |
      ~/.gradle/caches
      ~/.gradle/wrapper
    key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
    restore-keys: |
      gradle-${{ runner.os }}-
```

### Multiple Cache Strategy

Separate caches for different dependency types — finer invalidation.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      # Cache 1: npm dependencies
      - uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
        with:
          path: ~/.npm
          key: npm-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
          restore-keys: npm-${{ runner.os }}-

      # Cache 2: build output
      - uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
        with:
          path: dist
          key: build-${{ runner.os }}-${{ github.sha }}
          restore-keys: build-${{ runner.os }}-

      # Cache 3: Cypress binary
      - uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
        with:
          path: ~/.cache/Cypress
          key: cypress-${{ runner.os }}-${{ hashFiles('package-lock.json') }}

      - run: npm ci
      - run: npm run build
      - run: npx cypress run
```

### Cache Size Limits

- Max 10 GB per repo (all branches combined)
- Entries not accessed in 7 days evicted (LRU)
- Single entry max ~10 GB
- Too many keys → eviction pressure. Keep keys stable.

---

## OIDC for AWS

No long-lived AWS keys. GitHub OIDC provider issues short-lived token. AWS trusts token via IAM role.

### Workflow

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

permissions:
  id-token: write    # Required for OIDC token
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@ec61189 # v6.1.0
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          aws-region: us-east-1
          role-session-name: gha-deploy-${{ github.run_id }}

      - run: aws s3 sync dist/ s3://my-bucket/
      - run: aws cloudfront create-invalidation --distribution-id E1234 --paths "/*"
```

### AWS IAM Trust Policy

Trust policy locks to specific repo + branch + environment. Never use wildcard `*` for `sub` claim.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:environment:production"
        }
      }
    }
  ]
}
```

### Sub Claim Patterns

| Pattern | Matches |
|---------|---------|
| `repo:myorg/myrepo:ref:refs/heads/main` | Only main branch |
| `repo:myorg/myrepo:environment:production` | Only production environment |
| `repo:myorg/myrepo:ref:refs/tags/v*` | Any version tag |
| `repo:myorg/myrepo:pull_request` | Any PR (dangerous — avoid for deploy) |
| `repo:myorg/*:ref:refs/heads/main` | All repos in org, main branch |

### OIDC Setup Steps

1. Create OIDC provider in AWS IAM (one-time per account):
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
2. Create IAM role with trust policy above
3. Attach permission policies to role (least privilege)
4. Set `role-to-assume` in workflow

### Multi-Account OIDC

Different roles per environment. Same OIDC provider, different trust policies.

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@ec61189 # v6.1.0
        with:
          role-to-assume: arn:aws:iam::111111111111:role/staging-deploy
          aws-region: us-east-1

      - run: ./deploy.sh staging

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@ec61189 # v6.1.0
        with:
          role-to-assume: arn:aws:iam::222222222222:role/prod-deploy
          aws-region: us-east-1

      - run: ./deploy.sh production
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `@v2` tag pinning | Mutable, PPE risk | Pin to full SHA |
| `secrets: inherit` | All secrets exposed | Explicit secret passing |
| No `fail-fast: false` | One failure kills matrix | Set `fail-fast: false` |
| Giant monolithic workflow | Slow, hard to debug | Split into reusable workflows |
| Cache key without hash | Stale deps, broken builds | Use `hashFiles()` on lock files |
| Wildcard OIDC sub claim | Any repo/branch assumes role | Lock to repo+branch+environment |
| `permissions` not set | Default write-all | Set least-privilege per job |
| PR `run:` with untrusted input | Script injection | Use env vars, never interpolate event data |
| Long-lived AWS keys in secrets | Rotation burden, leak risk | OIDC federation |
| `cancel-in-progress: true` on deploy | Interrupted deploy = broken state | Only cancel on non-deploy jobs |

---

## Gotchas

- `workflow_call` caller and callee must be in same repo OR callee repo must be public/internal with Actions access
- Reusable workflow max 4 levels of nesting (not 10 — docs say 10 but practical limit lower due to token propagation)
- `hashFiles()` pattern relative to repo root, not working directory
- Cache `restore-keys` match longest prefix, not most recent
- OIDC `id-token: write` must be set at job level, not step level
- Composite action `shell:` required on every `run:` step — no default
- Matrix `include:` adds combos, `exclude:` removes — order matters
- `github.sha` in PR = merge commit SHA, not head commit. Use `github.event.pull_request.head.sha` for PR head
- `GITHUB_TOKEN` permissions reset per job. Set at workflow level or per-job
- `actions/cache` save happens at job end — if job fails, cache not saved. Use `actions/cache/save` + `actions/cache/restore` for explicit control
