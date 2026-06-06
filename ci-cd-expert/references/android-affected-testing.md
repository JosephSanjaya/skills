# Affected Module Detection & Test Architecture

## Git Diff Parsing

```bash
if [ "${{ github.event_name }}" = "pull_request" ]; then
  changed_files=$(git diff --name-only origin/main HEAD)
else
  changed_files=$(git diff --name-only HEAD~1 HEAD)
fi
```

## AffectedModuleDetector (Dropbox)

Hooks into Gradle task graph, applies `onlyIf` guard — no custom parsing needed.

```groovy
// root build.gradle.kts
plugins {
    id("com.dropbox.affectedmoduledetector") version "0.6.2"
}

affectedModuleDetector {
    baseDir = "${project.rootDir}"
    compareFrom = "SpecifiedBranchCommitMergeBase"
    specifiedBranch = "origin/main"
    pathsAffectingAllModules =
}
```

Run: `./gradlew runAffectedUnitTests -Paffected_module_detector.enable`

**Modular architecture tip**: "Abstract modules" (interfaces only) decouple feature modules from implementation → shorter compile path + parallel Gradle execution.

## Kover Coverage Reports

Aggregate reports in multi-module projects → high memory → OOM risk.

Fix: run sequentially per module, not concurrently:
```bash
./gradlew :module-a:koverXmlReportDevDebug
./gradlew :module-b:koverXmlReportDevDebug
```

## Test-Only Modules

Apply `com.android.test` plugin instead of `com.android.library`/`com.android.application`.

```groovy
android {
    targetProjectPath ':app'
    // declare matching build variants
}
```

Isolates heavy UI/instrumentation tests → exclude from PR loops → run nightly instead.

## Roborazzi Screenshot Testing

Running screenshot checks in generic `./gradlew test` = expensive image-render on every commit.

**Decouple strategy:**

1. **Bypass in general runs**: `./gradlew testDemoDebugUnitTest -Proborazzi.test.verify=false`
2. **On-demand**: separate workflow step triggered only on UI directory changes or `workflow_dispatch`
3. **Decoupled recording**: `./gradlew recordRoborazziDemoDebug` → store as transient GitHub Actions artifacts (not committed to git)

**Cache key precision**: GitHub Actions cache is immutable once created. Include commit SHA + lockfile hash + Gradle file hash in cache key to avoid stale restores.
