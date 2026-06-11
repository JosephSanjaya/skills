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
