# Concurrency Control & Release Pipelines

## Dynamic Concurrency Groups

Prevents multiple runs of same workflow wasting runner minutes when dev pushes sequential commits.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}
  cancel-in-progress: true
```

- `github.workflow`: scopes to specific workflow — prevents different pipelines (lint vs deploy) canceling each other
- `github.head_ref || github.run_id`: evaluates to branch name on PRs; falls back to unique `run_id` on main pushes (protects deployment sequences from self-canceling)
- `cancel-in-progress: true`: terminates active pipeline on branch when new commit pushed

Sequential deployments: use `queue: max` (up to 100 queued runs) — **cannot** combine with `cancel-in-progress: true`.

## Secure Keystore Signing

**Never commit keystore to repo. Store as encrypted GitHub Secrets.**

### Base64 approach (simpler)

Encode locally:
```bash
base64 -w 0 release.keystore > keystore.b64
```

Decode in workflow:
```yaml
- name: Decode Keystore
  env:
    KEYSTORE_B64: ${{ secrets.KEYSTORE_BASE64 }}
  run: |
    echo "$KEYSTORE_B64" | base64 -d > app/release.keystore
```

### GPG approach (stronger)

```yaml
- name: Decrypt Keystore via GPG
  run: |
    gpg -d --passphrase '${{ secrets.KEYSTORE_PASSPHRASE }}' --batch release.keystore.asc > app/release.keystore
```

### Dynamic keystore.properties

```yaml
- name: Configure Keystore Properties
  run: |
    echo "storeFile=release.keystore" >> keystore.properties
    echo "storePassword=${{ secrets.KEYSTORE_PASSWORD }}" >> keystore.properties
    echo "keyAlias=${{ secrets.KEY_ALIAS }}" >> keystore.properties
    echo "keyPassword=${{ secrets.KEY_PASSWORD }}" >> keystore.properties
```

Load in `build.gradle.kts`:
```kotlin
val keystorePropertiesFile = rootProject.file("keystore.properties")
val keystoreProperties = Properties()
if (keystorePropertiesFile.exists()) {
    keystorePropertiesFile.inputStream().use { keystoreProperties.load(it) }
}

signingConfigs {
    create("release") {
        storeFile = file(keystoreProperties.getProperty("storeFile") ?: "NOT_FOUND")
        storePassword = keystoreProperties.getProperty("storePassword")
        keyAlias = keystoreProperties.getProperty("keyAlias")
        keyPassword = keystoreProperties.getProperty("keyPassword")
    }
}
```

## Distribution

- QA builds: `wzieba/Firebase-Distribution-Github-Action`
- Play Store: `r0adkll/upload-google-play` with `./gradlew bundleRelease`
- Always run `chmod +x ./gradlew` early in workflow to prevent execution failures
