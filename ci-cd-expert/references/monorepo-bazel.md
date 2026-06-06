# Bazel Monorepo Reference

## Why Bazel

- **Hermetic builds** — tracks exact compiler binary, headers, env vars; sandbox isolates each action
- **Reproducible** — identical inputs = byte-for-byte identical outputs across machines
- **Remote execution** — shard builds across distributed workers (RBE)
- **Remote caching** — if anyone compiled same package, download cached binary instead of rebuilding
- **Polyglot** — native rules for Go, Java, C++, Python, Rust, Protocol Buffers; mix languages in single repo

## Presubmit Configuration (.bazelci/presubmit.yml)

```yaml
tasks:
  ubuntu2204:
    build_flags:
      - "--incompatible_enable_android_toolchain_resolution"
      - "--disk_cache=~/.cache/bazel"
    build_targets:
      - "//src/main/..."
    test_targets:
      - "//src/test/..."
    test_flags:
      - "--test_tag_filters=-integration-test"
      - "--flaky_test_attempts=3"
      - "--test_output=errors"
  rbe_ubuntu2204:
    shell_commands:
      - sed -i 's/^# rbe_preconfig/rbe_preconfig/' WORKSPACE.bazel
    build_targets:
      - "//..."
    test_targets:
      - "//..."
```

Key flags:

| Flag | Purpose |
|---|---|
| `--test_tag_filters=-integration-test` | Skip slow integration tests in presubmit |
| `--flaky_test_attempts=3` | Auto-retry flaky tests (network timeouts) |
| `--test_output=errors` | Only show failing test output |
| `--disk_cache=~/.cache/bazel` | Local disk cache path |
| `shell_commands` | Pre-build system config (sed, env setup) |

## Bzlmod (Modern Dependency Management)

Standard since Bazel 6.3/7+ (replaces monolithic `WORKSPACE` file). Marks repository root and lists external dependencies. Uses Minimal Version Selection (MVS) with the Bazel Central Registry (BCR).

### MODULE.bazel Example
```python
module(
  name = "my_project",
  version = "1.0.0",
)

# Direct dependencies from BCR
bazel_dep(name = "bazel_skylib", version = "1.7.1")
bazel_dep(name = "rules_go", version = "0.49.0")
bazel_dep(name = "gazelle", version = "0.38.0")
```

---

## Gazelle (Auto-Generate BUILD Files)

- Auto-generates Bazel rules for Go packages
- Minimal human input needed
- Run: `bazel run //:gazelle`
- Keeps BUILD files in sync with source; re-run after adding/removing files

## Enterprise Case Studies

### Uber (Go Monorepo)

- Polyglot: gRPC + Protocol Buffers + Go
- **SubmitQueue**: patches changes to HEAD of main for validation before landing
- Remote caching → halved CI build times
- Gazelle auto-generates most Go package rules

### Airbnb (JVM Monorepo)

- 4.5-year migration from Gradle → Bazel
- Tens of millions LOC (Java, Kotlin, Scala)

| Metric | Before (Gradle) | After (Bazel) |
|---|---|---|
| Local builds | 20+ min | 3-5x faster |
| CI p90 | 35 min | 2-3x faster |
| IDE sync | slow | 2-3x faster |
| Dev deploys | slow | 2-3x faster |
| Developer CSAT | 38% | 68% |

### Stripe (Ruby Monorepo)

- 50M-line Ruby codebase
- **Selective Test Execution (STE)**: instruments tests to record file access
- Builds file-level dependency graph
- Executes only **5% of test suite** per build (90%+ compute savings)
- Also migrated rubyfmt to Prism parser (skip Ruby VM → faster formatting)

## Anti-Patterns

| Anti-Pattern | Problem |
|---|---|
| No remote cache | Rebuilds everything locally every time |
| Overly broad test targets (`//...`) in presubmit | Runs entire repo on massive monorepos — CI timeout |
| No tag filtering | Mixes unit + integration tests; slow presubmit |
| No `flaky_test_attempts` | Intermittent failures block PRs |
| Skipping Gazelle | Manual BUILD file maintenance → drift, stale deps |
