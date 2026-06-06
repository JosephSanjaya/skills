# Monorepo CI/CD — Turborepo & Nx

## Turborepo (turbo.json)

Full config:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "futureFlags": {
    "globalConfiguration": true
  },
  "global": {
    "inputs": [".env", "pnpm-lock.yaml", "tsconfig.base.json"]
  },
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "lint": { "outputs": [] },
    "dev": { "cache": false, "persistent": true }
  }
}
```

### Key Concepts

- `^build` = topological dependency — upstream deps build first
- `outputs` = what gets cached
  - Empty array `[]` = cache logs only
  - Omit key entirely = cache nothing
- `cache: false` + `persistent: true` = dev servers (long-running, never cached)
- `global.inputs` = files that invalidate ALL task caches when changed
- Environment variable handling:
  - `$TURBO_DEFAULT$` = default env input set
  - Per-task env vars via `env` key in task config
- Remote cache: Vercel Remote Cache (hosted) or self-hosted (e.g., ducktape, turborepo-remote-cache)

### Gotchas

- Forgetting `outputs` → silent cache miss, builds always re-run
- `.next/cache/**` negation critical — Next.js cache is huge, non-deterministic
- `global.inputs` too broad (e.g., `**/*.ts`) = cache never hits
- No IO tracing — cache poisoning possible if task writes outside declared `outputs`
- Lockfile MUST be in `global.inputs` or dependency changes won't bust cache

### CI Pattern (GitHub Actions)

```yaml
- uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306 # v5.0.3
  with:
    path: node_modules/.cache/turbo
    key: turbo-${{ runner.os }}-${{ hashFiles('pnpm-lock.yaml') }}
    restore-keys: turbo-${{ runner.os }}-

- run: pnpm turbo run build test lint --filter=...[origin/main]
```

`--filter=...[origin/main]` = run only packages changed since main (affected).

---

## Nx (nx.json)

Full config:

```json
{
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "sharedGlobals": ["{workspaceRoot}/.github/workflows/ci.yml"],
    "production": [
      "default",
      "!{projectRoot}/**/?(*.)+(spec|test).[jt]s?(x)?(.snap)",
      "!{projectRoot}/tsconfig.spec.json",
      "!{projectRoot}/jest.config.[jt]s"
    ]
  },
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["production", "^production"],
      "outputs": ["{projectRoot}/dist"],
      "cache": true
    },
    "test": {
      "inputs": ["default", "^production"],
      "cache": true
    }
  }
}
```

### Key Concepts

- `namedInputs` = reusable input sets, composable via references
  - `production` excludes test files → test-only changes don't invalidate build cache
  - `^production` = upstream deps use production inputs too
- `targetDefaults` = repo-wide task rules (overridable per-project in `project.json`)
- IO tracing = Nx tracks actual file reads/writes, detects cache poisoning
- `cache: true` = opt-in per target (unlike Turborepo default-on)
- Nx Cloud features:
  - Distributed task execution across CI agents
  - Self-healing CI (auto-retry flaky)
  - Flaky test detection and quarantine
- Affected command: `nx affected --target=build --base=main` — only runs changed + dependents

### Gotchas

- `namedInputs` composition order matters — negation patterns must come AFTER base set
- Missing `cache: true` = target never cached (silent perf loss)
- `{projectRoot}` vs `{workspaceRoot}` confusion = wrong cache scope
- Nx daemon must be running for perf — `NX_DAEMON=true` (default in Nx 15+)
- Large `sharedGlobals` set = frequent full rebuilds

### CI Pattern (GitHub Actions)

```yaml
- uses: nrwl/nx-set-shas@v4

- run: npx nx affected --target=lint --base=$NX_BASE --head=$NX_HEAD
- run: npx nx affected --target=test --base=$NX_BASE --head=$NX_HEAD
- run: npx nx affected --target=build --base=$NX_BASE --head=$NX_HEAD
```

`nrwl/nx-set-shas` = sets `NX_BASE`/`NX_HEAD` SHAs correctly for PRs and main branch.

---

## Comparison

| Feature | Turborepo | Nx |
|---|---|---|
| Setup time | ~15 min | Hours |
| Caching | Default on, flat inputs | Opt-in, composable namedInputs |
| Polyglot | Via package.json scripts | Native graph (JS/TS/Java/.NET/Rust/Python) |
| Task sandboxing | No | IO tracing + cache poison protection |
| CI solution | Manual binning | Nx Cloud (distributed) |
| Affected detection | `--filter=...[base]` | `nx affected --base=main` |
| Cache granularity | Global deps + per-task outputs | namedInputs composable sets |
| Best for | Speed, simple monorepos | Governance, complex polyglot repos |

## Anti-Patterns

- ❌ Running full `turbo run build` without `--filter` on CI — rebuilds everything
- ❌ Caching `dev` or `serve` tasks — wastes storage, never hits
- ❌ Sharing remote cache between branches without scoping — cache poisoning risk
- ❌ Nx: forgetting `--base` on `affected` — defaults to last commit only, misses PR changes
- ❌ Both: not pinning package manager version in CI — lockfile drift busts cache
