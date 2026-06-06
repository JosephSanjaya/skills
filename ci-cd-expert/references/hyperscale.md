# Hyperscale CI/CD Patterns

## Stripe

- **Scale**: 50M lines of Ruby code, 100k+ tests.
- **Selective Test Execution (STE)**:
  - Instruments test framework to track which files are accessed during each test run.
  - Builds comprehensive file-to-test dependency graph.
  - On PR, runs Git diff, finds changed files, calculates union of impacted tests.
  - Executes ~5% of the test suite per commit. Prevents runtimes of hours, cuts compute costs by 90%+.
- **Formatting**: Replaced standard Ruby parser with Prism in `rubyfmt`. Avoids starting slow Ruby VM, results in fast formatting checks in CI.
- **Migrated 3.7M lines** of JS to TS in a single PR using codemods and optimized build graphs.

---

## Uber

- **Scale**: Massive Go monorepo, hundreds of microservices.
- **Tooling**: Bazel for hermetic, reproducible multi-language builds.
- **SubmitQueue**:
  - Validates PR merges sequentially against the latest HEAD of master.
  - Tests code in speculative state before committing to target branch.
  - Prevents broken master branch scenarios common in high-concurrency codebases.
- **Gazelle**: Generates Bazel rules for Go packages automatically from source imports.

---

## Airbnb

- **Scale**: Monorepo with tens of millions of Java, Kotlin, and Scala lines.
- **Migration**: 4.5-year effort transitioning JVM build ecosystem from Gradle to Bazel.
- **Results**:
  - Local build times decreased 3-5x.
  - IDE sync and compilation times cut 2-3x.
  - Developer CSAT increased from 38% to 68%.

---

## Netflix

- **Orchestration**: Built Spinnaker to replace Asgard, enabling multi-cloud continuous delivery to AWS, GCP, and Kubernetes.
- **Automated Canary Analysis**: Co-developed Kayenta with Google.
  - Compares telemetry between canary instances and production baseline.
  - Auto-promotes changes if statistical scores pass; executes auto-rollback instantly if metrics spike.
- **ChAP (Chaos Automation Platform)**: Automates chaos engineering experiments (traffic injection, failures) inside production pipelines to verify resiliency.
