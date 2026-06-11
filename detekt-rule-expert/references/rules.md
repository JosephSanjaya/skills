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

## 3. Type Resolution (Analysis API)

Type resolution allows querying compiler symbols, smart casts, and fully-resolved types instead of raw syntax.

### Detekt 1.x (K1 Compiler)
Requires implementing `RequiresFullAnalysis`. Access via `bindingContext`.
```kotlin
import io.gitlab.arturbosch.detekt.api.RequiresFullAnalysis
import org.jetbrains.kotlin.resolve.BindingContext

class MyTypeRule(config: Config) : Rule(config), RequiresFullAnalysis {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (bindingContext == BindingContext.EMPTY) return // Guard against light analysis
        val type = function.typeReference?.getType(bindingContext)
        // ...
    }
}
```

### Detekt 2.0 (K2 Compiler & Analysis API)
Requires implementing `RequiresAnalysisApi`. Wrap resolution inside `analyze(element)`.
```kotlin
import dev.detekt.api.RequiresAnalysisApi
import org.jetbrains.kotlin.analysis.api.analyze
import org.jetbrains.kotlin.analysis.api.types.KaFunctionType

class MyTypeRule(config: Config) : Rule(config, "desc"), RequiresAnalysisApi {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        analyze(function) {
            val returnType = function.symbol.returnType
            if (returnType is KaFunctionType) {
                // ...
            }
        }
    }
}
```

#### API Translation Mapping (1.x -> 2.0)
| 1.x (K1) | 2.0 (K2 Analysis API inside `analyze {}`) |
| :--- | :--- |
| `expression.getType(bindingContext)` | `expression.expressionType` |
| `bindingContext[REFERENCE_TARGET, ref]` | `ref.mainReference.resolveToSymbol()` |
| `expression.getResolvedCall(bindingContext)` | `expression.resolveToCall().successfulCallOrNull()` |
| `DeclarationDescriptor` | `KaSymbol` (obtained via `element.symbol`) |
| `KotlinType` | `KaType` |

---

## 4. Auto-Correction

Auto-correction mutates the PSI tree. It is only executed when auto-correct is globally enabled.

- **Precondition**: Verify safety (e.g. check for nullable safe-calls, types, etc.) before replacing.
- **Block wrapper**: Wrap mutations inside `withAutoCorrect { ... }`.
- **Node Replacement**: Use `KtPsiFactory` to build new AST nodes, then call `astReplace(newElement)`.

```kotlin
import dev.detekt.api.ext.astReplace
import org.jetbrains.kotlin.psi.KtPsiFactory

// Inside visitCallExpression:
if (canFixSafely) {
    withAutoCorrect {
        val newCall = KtPsiFactory.contextual(expression)
            .createExpression("newFunctionCall()")
        expression.astReplace(newCall)
    }
}
```

---

## 5. ServiceLoader Configuration

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

## 6. Testing Rules

Use `detekt-test` module to assert findings.

### AST/Syntax Rules (No Context)
```kotlin
import dev.detekt.test.TestConfig
import io.gitlab.arturbosch.detekt.api.Config
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class MyCustomRuleTest {
    private val rule = MyCustomRule(Config.empty)

    @Test
    fun `reports invalid cases`() {
        val code = """
            fun forbidden() { }
        """.trimIndent()
        
        val findings = rule.lint(code)
        assertThat(findings).hasSize(1)
        assertThat(findings.first().message).contains("Forbidden name")
    }
}
```

### Type Resolution Rules (With Context)
Requires injecting the compiler environment container.

- **Detekt 1.x**: `@KotlinCoreEnvironmentTest` annotation + `KotlinCoreEnvironment` parameter.
- **Detekt 2.0**: `@KotlinCoreEnvironmentTest` annotation + `KotlinEnvironmentContainer` parameter.

```kotlin
import dev.detekt.test.KotlinEnvironmentContainer
import dev.detekt.test.KotlinCoreEnvironmentTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

@KotlinCoreEnvironmentTest
class MyTypeRuleTest(private val env: KotlinEnvironmentContainer) {
    private val rule = MyTypeRule(Config.empty)

    @Test
    fun `reports invalid types`() {
        val code = """
            val x: Int = 123
        """.trimIndent()
        
        val findings = rule.lintWithContext(env, code)
        assertThat(findings).hasSize(1)
    }
}
```
