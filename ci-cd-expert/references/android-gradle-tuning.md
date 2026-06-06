# Gradle Tuning & Caching

## Compiler Tuning

**KSP > kapt**: KSP runs as Kotlin compiler plugin, skips expensive Java stub generation. Migrate kapt → KSP where possible.

**Legacy kapt**: enable incremental annotation processing + kapt build cache. Note: kapt incremental is fragile — falls back to full rebuild on non-ABI changes, resource ID additions, or JDK mismatches. JDK version must match between local dev and CI runner.

**Toolchain upgrades**: AGP + Kotlin compiler + Gradle Wrapper updates yield major perf gains.
- Example: Gradle 8.10 → 9.5.1 cuts clean compile 21s → 8s on reference project.

**Daemon persistence**: Client JVM args must match daemon args or Gradle spawns disposable single-use daemon (loses warm-state gains across steps in same runner).

**Repo declaration order**: Gradle resolves repos sequentially. Core libs/Android plugins live on Google + Maven Central → put `gradlePluginPortal()` **last** to avoid redundant lookups.

## Configuration Cache

Serializes task execution graph → skips config phase on subsequent runs if build scripts unchanged.

**Security risk**: serialized graph may capture env vars, credentials → never store unencrypted.

```yaml
- name: Setup Gradle Environment
  uses: gradle/actions/setup-gradle@v6
  with:
    gradle-version: wrapper
    cache-encryption-key: ${{ secrets.GRADLE_CACHE_ENCRYPTION_KEY }}
    gradle-home-cache-cleanup: true
```

Generate key: `openssl rand -base64 16` → store as repo secret.

Tasks must not reference live JVM state, Gradle Project models, or custom listeners at execution time. Query env vars via `providers.environmentVariablesPrefixedBy`, not direct system calls.

**Avoid**: `actions/cache` or `actions/setup-java cache: gradle` — lack wrapper checksum validation, cache cleanup, and advanced cache keys that `setup-gradle` provides.

## Local Build Cache Isolation

Global `GRADLE_USER_HOME` cache → cross-contamination + file locking when parallel jobs run.

```groovy
// settings.gradle
buildCache {
    local {
        directory = File(rootDir, ".gradle-local-cache")
    }
}
```

## Remote HTTP Build Cache

```groovy
buildCache {
    remote(HttpBuildCache) {
        url = 'https://enterprise-cache.local:8123/cache/'
        credentials {
            username = 'build-cache-user'
            password = 'some-complicated-password'
        }
        isAllowUntrustedServer = true
        isUseExpectContinue = true  // checks server accepts payload before transmitting body
    }
}
```

## Dynamic Cache Read-Only Strategy

Feature branches read-only → prevents polluting main cache baseline.

```yaml
- name: Setup Gradle with Dynamic Caching
  uses: gradle/actions/setup-gradle@v6
  with:
    cache-read-only: ${{ github.ref != 'refs/heads/main' && github.ref != 'refs/heads/release' }}
```

**Cache throughput**: GitHub Actions cache tops out at 50-100 MB/s. Use RunsOn or Depot Cache (S3/Azure Blob in same VPC) for 300-500 MB/s.

**Cache size**: As of Nov 20, 2025 — can exceed default 10GB with pay-as-you-go. Budget limit hit → reverts to read-only automatically.

| Cache Layer | Storage | Invalidation Trigger | Security |
|-------------|---------|---------------------|----------|
| Gradle Build Cache | Local dir or Remote HTTP key-value | Task input file hash, compiler args, source changes | Local isolation; HTTPS + gateway for remote |
| Gradle Config Cache | Serialized task graph on disk | build.gradle.kts changes, version catalog, env vars | Encrypt via `cache-encryption-key` |
