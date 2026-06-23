# Custom Detekt Rules: Unit Testing

Custom Detekt rules are tested using the `detekt-test` module to verify syntax violations, type-based findings, and custom ruleset behaviors.

## 1. Syntax/AST Rules (No Context)
Use the `Rule.lint(String)` extension method. It parses the snippet into a temporary file without type resolution.

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

## 1a. Autocorrect Testing Pitfalls

**Entity anchor must survive mutation.** When the rule deletes or moves the reported element, reading `findings.first().entity.ktElement?.containingFile?.text` returns `null` or the pre-mutation text. Use a stable parent as the entity anchor (see `autocorrect.md §3a`).

**Substring matching in fixed text.** `indexOf("val name")` matches inside `const val name`. Always use a more specific substring, e.g. `indexOf("val name =")` to avoid false positives.

```kotlin
// Wrong — matches "const val name" too
val nameIndex = fixed.indexOf("val name")

// Correct — unique to non-const property
val nameIndex = fixed.indexOf("val name =")
```

**Node copy for move operations.** Use `element.copy()` not `factory.createProperty(element.text)` to clone PSI nodes with modifiers intact (see `autocorrect.md §3b`).

## 2. Type Resolution Rules (With Context)
Requires injecting the compiler environment container to build type symbols.
- **Detekt 1.x**: Annotate the class with `@KotlinCoreEnvironmentTest` and inject a `KotlinCoreEnvironment` parameter.
- **Detekt 2.0**: Annotate the class with `@KotlinCoreEnvironmentTest` and inject a `KotlinEnvironmentContainer` parameter.

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

---

## Quick Reference: Testing Pitfalls

| Pitfall | Wrong | Correct |
|---|---|---|
| Entity on deleted element | `findings.first().entity.ktElement?.containingFile` returns null | Anchor entity to stable parent; read file text via that node |
| Substring match in fixed text | `indexOf("val name")` matches `const val name` | `indexOf("val name =")` — include `=` to narrow match |
| Autocorrect config | `Config.empty` — autocorrect never fires | `TestConfig("autoCorrect" to true)` |
| Type resolution without context | `rule.lint(code)` — no type info | `rule.lintWithContext(env, code)` with `@KotlinCoreEnvironmentTest` |
