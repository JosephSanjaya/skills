# Custom Detekt Rules: Implementation & API Reference

## 1. Core Mechanics: PSI & AST Visitors

Detekt parses Kotlin code into Program Structure Interface (PSI) trees. Custom rules walk this tree using visitor callbacks.

```
KtFile (visitKtFile)
  ├── KtClass (visitClass)
  ├── KtNamedFunction (visitNamedFunction)
  └── KtCallExpression (visitCallExpression)
```

- **Visitor Base**: Override narrowest callback (e.g., `visitNamedFunction` instead of generic `visitDeclaration`).
- **AST Descent**: Call `super.visitXXX()` to continue traversing child nodes. Omitting it stops descent.
- **Node Resolution**: Use helper functions to check modifiers, receivers, or annotations (e.g. `isComposable()`).

---

## 2. API Differences: Detekt 1.x vs Detekt 2.0

| Feature | Detekt 1.x | Detekt 2.0 |
| :--- | :--- | :--- |
| **Package** | `io.gitlab.arturbosch.detekt.api` | `dev.detekt.api` |
| **Base Class** | `Rule(config)` | `Rule(config, description)` |
| **Metadata** | `Issue` object in rule class | Passed to rule constructor |
| **Reporting** | `report(CodeSmell(issue, entity, message))` | `report(Finding(entity, message))` |
| **Type resolution interface** | `RequiresFullAnalysis` or `@RequiresTypeResolution` | `RequiresAnalysisApi` |
| **Type resolution access** | `bindingContext` (`BindingContext`) | Kotlin Analysis API (`analyze(element) { ... }`) |
| **ServiceLoader path** | `META-INF/services/io.gitlab.arturbosch.detekt.api.RuleSetProvider` | `META-INF/services/dev.detekt.api.RuleSetProvider` |

### Detekt 1.x Code Template
```kotlin
package com.example.rules

import io.gitlab.arturbosch.detekt.api.Config
import io.gitlab.arturbosch.detekt.api.Rule
import io.gitlab.arturbosch.detekt.api.Issue
import io.gitlab.arturbosch.detekt.api.Severity
import io.gitlab.arturbosch.detekt.api.Debt
import io.gitlab.arturbosch.detekt.api.CodeSmell
import io.gitlab.arturbosch.detekt.api.Entity
import org.jetbrains.kotlin.psi.KtNamedFunction

class MyCustomRule(config: Config) : Rule(config) {
    override val issue = Issue(
        javaClass.simpleName,
        Severity.CodeSmell,
        "Description of rule.",
        Debt.FIVE_MINS
    )

    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (function.name == "forbidden") {
            report(CodeSmell(issue, Entity.from(function), "Forbidden name."))
        }
    }
}
```

### Detekt 2.0 Code Template
```kotlin
package com.example.rules

import dev.detekt.api.Config
import dev.detekt.api.Rule
import dev.detekt.api.Entity
import dev.detekt.api.Finding
import dev.detekt.api.RuleName
import org.jetbrains.kotlin.psi.KtNamedFunction

class MyCustomRule(config: Config) : Rule(config, "Description of rule.") {
    override val ruleName: RuleName = RuleName("MyCustomRule")

    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (function.name == "forbidden") {
            report(Finding(Entity.from(function), "Forbidden name."))
        }
    }
}
```

---

## 3. ServiceLoader Configuration

Every custom rule set needs a provider registered via Java's `ServiceLoader`.

### Provider Implementation
```kotlin
import dev.detekt.api.Config
import dev.detekt.api.RuleSet
import dev.detekt.api.RuleSetId
import dev.detekt.api.RuleSetProvider
import dev.detekt.api.RuleName

class CustomRuleSetProvider : RuleSetProvider {
    override val ruleSetId = RuleSetId("my-ruleset")
    override fun instance(): RuleSet = RuleSet(
        ruleSetId,
        listOf(
            MyCustomRule(Config.empty)
        )
    )
}
```

### Registration File
Create a text file containing the fully-qualified class name of your `RuleSetProvider`.

- **Detekt 1.x**:
  `src/main/resources/META-INF/services/io.gitlab.arturbosch.detekt.api.RuleSetProvider`
  ```text
  com.example.rules.CustomRuleSetProvider
  ```
- **Detekt 2.0**:
  `src/main/resources/META-INF/services/dev.detekt.api.RuleSetProvider`
  ```text
  com.example.rules.CustomRuleSetProvider
  ```

---

## 3b. `valueOrDefault` Must Be Called After `issue` Is Initialized

`valueOrDefault(key, default)` calls `ruleId`, which reads `issue.getId()`. If invoked before `issue` is set (e.g., as a property initializer), it throws `NullPointerException`:

```
NullPointerException: Cannot invoke "Issue.getId()" because getIssue() is null
```

**Rule:** always wrap `valueOrDefault` calls in `by lazy {}`:

```kotlin
// Wrong — evaluated before issue is set
private val threshold = valueOrDefault("threshold", 10)

// Correct — deferred until first use, after issue is initialized
private val threshold by lazy { valueOrDefault("threshold", 10) }
```

This applies to all config reads: strings, ints, booleans, and lists.

---

## 3c. Reading List Config Values

`valueOrDefault` accepts a typed default. For list config keys, pass an empty typed list:

```kotlin
// detekt-config.yml
// my-ruleset:
//   MyRule:
//     sourcePaths:
//       - path/to/file1.kt
//       - path/to/file2.kt

private val sourcePaths by lazy { valueOrDefault("sourcePaths", emptyList<String>()) }
```

In `TestConfig`, pass an actual `List<String>`:

```kotlin
TestConfig("sourcePaths" to listOf("path/to/file1.kt", "path/to/file2.kt"))
```

---

## 3d. `associate` Takes Last Match — Use `putIfAbsent` for First-Wins

When building a map from regex matches where multiple entries share the same key (e.g., several `val foo = 16.dp` properties), Kotlin's `associate {}` keeps the **last** match. Use `putIfAbsent` to keep the **first**:

```kotlin
// Wrong — last 16.dp property wins (e.g., cornerRadiusCard instead of standardPadding)
return matches.associate { it.groupValues[2] to it.groupValues[1] }

// Correct — first occurrence wins (value type here is String; use your own value type as needed)
val seen = mutableSetOf<String>()
val result = mutableMapOf<String, String>()
matches
    .filter { seen.add(it.groupValues[2]) }
    .forEach { result.putIfAbsent(it.groupValues[2], it.groupValues[1]) }
```

---

## 4. Other Guide References

For advanced topics, refer to the following dedicated manuals:
- **Type Resolution (Analysis API)**: [types.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/types.md)
- **Auto-Correction & AST Mutation**: [autocorrect.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/autocorrect.md)
- **Unit Testing Rules**: [testing.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/testing.md)
- **Reports & Output Presentation**: [reports.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/reports.md)
- **Baseline Suppression Support**: [baseline.md](file:///Users/jsanjaya/.gemini/config/skills/detekt-rule-expert/references/baseline.md)
