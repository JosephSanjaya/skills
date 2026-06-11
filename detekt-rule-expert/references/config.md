# Detekt Configuration & Suppression Reference

## 1. YAML Configuration Schema (`detekt.yml`)

The basic structure configures rulesets, rules, and global properties.

```yaml
config:
  validation: true # Verifies config keys against default-detekt-config.yml
  excludes: "custom-ruleset.*" # Exclude custom properties from validation

custom-ruleset:
  active: true
  MyCustomRule:
    active: true
    severity: warning # warning | error | info
    threshold: 10
```

---

## 2. Configuration Validation Exclusion

Detekt validates YAML keys. Custom rulesets with dynamic parameters will trigger validation errors. Exclude them under the `config` block.

```yaml
config:
  validation: true
  # Excludes the custom ruleset and all its child properties from validation
  excludes: "Compose.*,Compose>.*>.*"
```

---

## 3. Ignoring Generated Code (CI Optimization)

Avoid analyzing generated code (e.g., KSP, KAPT, ViewBinding). Exclude directories at the Gradle task level.

```kotlin
// build.gradle.kts
tasks.withType<dev.detekt.gradle.plugin.tasks.Detekt>().configureEach {
    exclude { it.file.invariantSeparatorsPath.contains("/build/generated/") }
}

tasks.withType<dev.detekt.gradle.plugin.tasks.DetektCreateBaselineTask>().configureEach {
    exclude { it.file.invariantSeparatorsPath.contains("/build/generated/") }
}
```

---

## 4. Suppression Annotations

Code smells can be suppressed at the declaration or file level using `@Suppress` or `@SuppressWarnings`.

- **Rule suppression**: `@Suppress("RuleId")`
- **Ruleset suppression**: `@Suppress("RulesetId:RuleId")`
- **Detekt prefix**: `@Suppress("detekt:RuleId")`

### Examples

#### Declaration Level Suppression
```kotlin
@Suppress("TooManyFunctions")
class ComplexComponent {
    // Detekt will ignore TooManyFunctions rule in this class
}
```

#### File Level Suppression
```file
@file:Suppress("Naming") // Suppresses all naming rules in this file
package com.example.app
```

#### Multi-Tool Suppression
```kotlin
@Suppress("detekt:ModifierMissing", "AndroidLintModifierMissing")
@Composable
fun LegacyView() { ... }
```

---

## 5. Severity Levels Configuration

Detekt 2.0 configures severity exclusively via the YAML file, overriding any coded defaults.

```yaml
style:
  MagicNumber:
    active: true
    severity: info # Reports as info, does not fail build in threshold checks
  
complexity:
  TooManyFunctions:
    active: true
    severity: error # Fails the build if found in CI
```
- **error**: Fails build if threshold exceeded.
- **warning**: Emits diagnostic warning.
- **info**: Diagnostic log, no impact on build status.
