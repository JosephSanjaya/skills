# Custom Detekt Rules: Auto-Correction & Headless Testing

Auto-correction mutates the PSI tree. It only runs when `autoCorrect = true` in the rule's config.

## 1. API Differences: 1.x vs 2.x

| | Detekt 1.x (≤1.23.x) | Detekt 2.x |
|---|---|---|
| Wrap mutation | `withAutoCorrect { }` | `withAutoCorrect { }` |
| Replace node | `element.replace(newElement)` | `element.astReplace(newElement)` |
| Import for replace | `org.jetbrains.kotlin.psi.PsiElement` (stdlib) | `import dev.detekt.api.ext.astReplace` |
| PSI factory | `KtPsiFactory(element.project)` | `KtPsiFactory.contextual(element)` |

## 2. PSI Package: Shaded Location in kotlin-compiler-embeddable

`kotlin-compiler-embeddable` shades IntelliJ PSI under `org.jetbrains.kotlin.com.intellij.*`.
Use this prefix — **not** `com.intellij.*` — or the import will be unresolved at compile time.

```kotlin
// Correct for detekt-api compileOnly + kotlin-compiler-embeddable
import org.jetbrains.kotlin.com.intellij.psi.PsiWhiteSpace
import org.jetbrains.kotlin.com.intellij.psi.PsiElement

// Wrong — com.intellij.* not on classpath when detekt-api is compileOnly
import com.intellij.psi.PsiWhiteSpace  // Unresolved reference 'psi'
```

`KtPsiFactory` lives in `org.jetbrains.kotlin.psi.KtPsiFactory` (unshaded) — import as-is.

## 3. Implementation Pattern (Detekt 1.x)

```kotlin
import org.jetbrains.kotlin.com.intellij.psi.PsiWhiteSpace
import org.jetbrains.kotlin.psi.KtPsiFactory

// Inside a visit* callback:
if (!hasBlankLine) {
    report(CodeSmell(issue, Entity.from(element), "..."))
    withAutoCorrect {
        val whiteSpace = element.prevSibling as? PsiWhiteSpace ?: return@withAutoCorrect
        val indent = whiteSpace.text.substringAfterLast('\n')
        whiteSpace.replace(KtPsiFactory(element.project).createWhiteSpace("\n\n$indent"))
    }
}
```

Key points:
- `withAutoCorrect` block runs only when `autoCorrect = true` in config — safe to always include.
- `report()` must be called **before** `withAutoCorrect {}` — the finding is needed regardless.
- Mutate the **whitespace node between siblings**, not the element itself.
- `substringAfterLast('\n')` preserves existing indentation level.

## 4. Implementation Pattern (Detekt 2.x)

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

## 5. Testing Auto-Correction (Detekt 1.x)

No complex environment setup needed. Use `TestConfig("autoCorrect" to true)` and inspect the mutated `ktElement?.containingFile?.text` from the finding.

```kotlin
import io.gitlab.arturbosch.detekt.test.TestConfig
import io.gitlab.arturbosch.detekt.test.lint
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MyRuleAutoCorrectTest {
    @Test
    fun `autocorrects missing blank line`() {
        val rule = MyRule(TestConfig("autoCorrect" to true))
        val code = """
            fun compute(): Int {
                val x = calculate()
                return x
            }
        """.trimIndent()

        val findings = rule.lint(code)
        assertEquals(1, findings.size)

        // After lint(), PSI is mutated in-place — read from the finding's ktElement
        val fixed = findings.first().entity.ktElement?.containingFile?.text ?: ""
        assertTrue("blank line not inserted", fixed.contains("calculate()\n\n"))
    }
}
```

`TestConfig` constructor (1.x): `TestConfig(vararg pairs: Pair<String, Any>)` — no annotation or env injection needed for AST-only rules.

**How it works:** `lint()` calls `visitFile()` which runs the visitor. `withAutoCorrect {}` fires during the visit and mutates the PSI in-place. The finding's `entity.ktElement` points into the same (now mutated) file, so reading `containingFile.text` after `lint()` returns the fixed source.

## 6. Testing Auto-Correction (Detekt 2.x — Headless Compiler Environment)

In headless compiler test environments (such as those using `@KotlinCoreEnvironmentTest` and `@KotlinAnalysisApiEngineTest`), mutating the AST via `PsiElement.replace` triggers exceptions due to unregistered extensions and missing application/project services (`TreeCopyHandler`, `IndentHelper`, `PomModel`).

To run auto-correct tests successfully, register these mocks and stub services on the test environment context before running `lint`:

```kotlin
import dev.detekt.test.TestConfig
import dev.detekt.test.junit.KotlinAnalysisApiEngineTest
import dev.detekt.test.junit.KotlinCoreEnvironmentTest
import dev.detekt.test.utils.KotlinAnalysisApiEngine
import dev.detekt.test.utils.KotlinEnvironmentContainer
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

@KotlinCoreEnvironmentTest
@KotlinAnalysisApiEngineTest
class MyAutoCorrectSpec(
    private val env: KotlinEnvironmentContainer,
    private val analysisApiEngine: KotlinAnalysisApiEngine,
) {
    @Test
    fun `auto-corrects code`() {
        val rule = MyCustomRule(TestConfig("autoCorrect" to true))
        val code = """
            fun oldStyle() { }
        """.trimIndent()

        val ktFile = analysisApiEngine.compile(
            code = code,
            javaSourceRoots = env.javaSourceRoots,
            jvmClasspathRoots = env.jvmClasspathRoots,
            allowCompilationErrors = true
        )

        // 1. Register TreeCopyHandler extension point on root ExtensionsArea
        try {
            val rootArea = com.intellij.openapi.extensions.Extensions.getRootArea()
            if (!rootArea.hasExtensionPoint("com.intellij.treeCopyHandler")) {
                com.intellij.core.CoreApplicationEnvironment.registerExtensionPoint(
                    rootArea,
                    com.intellij.openapi.extensions.ExtensionPointName.create<com.intellij.psi.impl.source.tree.TreeCopyHandler>("com.intellij.treeCopyHandler"),
                    com.intellij.psi.impl.source.tree.TreeCopyHandler::class.java
                )
            }
        } catch (e: Throwable) {
            e.printStackTrace()
        }

        // 2. Register IndentHelper service on ApplicationManager
        try {
            val app = com.intellij.openapi.application.ApplicationManager.getApplication()
            if (app != null) {
                val serviceClass = com.intellij.psi.impl.source.codeStyle.IndentHelper::class.java
                if (app.getService(serviceClass) == null) {
                    val instance = object : com.intellij.psi.impl.source.codeStyle.IndentHelper() {
                        override fun getIndent(file: com.intellij.psi.PsiFile, node: com.intellij.lang.ASTNode): Int = 0
                        override fun getIndent(file: com.intellij.psi.PsiFile, node: com.intellij.lang.ASTNode, includeNonSpace: Boolean): Int = 0
                    }
                    val method = app.javaClass.getMethod("registerService", Class::class.java, Any::class.java)
                    method.invoke(app, serviceClass, instance)
                }
            }
        } catch (e: Throwable) {
            e.printStackTrace()
        }

        // 3. Register PomModel service on Project (resolving TreeAspect)
        try {
            val project = ktFile.project
            val pomModelClass = com.intellij.pom.PomModel::class.java
            if (project.getService(pomModelClass) == null) {
                val treeAspect = com.intellij.pom.tree.TreeAspect()
                val instance = object : com.intellij.pom.PomModel {
                    private val userDataMap = mutableMapOf<com.intellij.openapi.util.Key<*>, Any?>()

                    override fun <T : Any?> getUserData(key: com.intellij.openapi.util.Key<T>): T? {
                        @Suppress("UNCHECKED_CAST")
                        return userDataMap[key] as T?
                    }
                    override fun <T : Any?> putUserData(key: com.intellij.openapi.util.Key<T>, value: T?) {
                        if (value == null) userDataMap.remove(key) else userDataMap[key] = value
                    }
                    override fun <T : com.intellij.pom.PomModelAspect> getModelAspect(aspectClass: Class<T>): T? {
                        if (aspectClass.name == "com.intellij.pom.tree.TreeAspect") {
                            @Suppress("UNCHECKED_CAST")
                            return treeAspect as T
                        }
                        return project.getService(aspectClass)
                    }
                    override fun runTransaction(transaction: com.intellij.pom.PomTransaction) {
                        transaction.run()
                    }
                }
                val method = project.javaClass.getMethod("registerService", Class::class.java, Any::class.java)
                method.invoke(project, pomModelClass, instance)
            }
        } catch (e: Throwable) {
            e.printStackTrace()
        }

        // 4. Run rule and assert correct output
        rule.lint(ktFile)

        val expected = """
            fun newStyle() { }
        """.trimIndent()
        assertEquals(expected, ktFile.text)
    }
}
```

## 7. Baseline vs AutoCorrect

Baseline and autocorrect operate at **different layers** — they do not communicate:

- `withAutoCorrect {}` runs in the **visitor phase** — PSI mutation happens when the rule fires.
- Baseline runs in the **reporting phase** — filters which findings cause CI failure.

A finding suppressed by baseline still triggers `withAutoCorrect {}`. There is no way in Detekt 1.x to skip autocorrect for baselined items. Use `@Suppress("RuleName")` at call sites to suppress both.