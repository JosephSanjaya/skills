# Custom Detekt Rules: Auto-Correction & Headless Testing

Auto-correction mutates the PSI tree of the parsed code. It is only executed when auto-correct is globally enabled.

## 1. Implementation
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

## 2. Testing Auto-Correction (AST Mutation in Headless Environment)

In headless compiler test environments (such as those using `@KotlinCoreEnvironmentTest` and `@KotlinAnalysisApiEngineTest`), mutating the AST via `PsiElement.replace` triggers exceptions due to unregistered extensions and missing application/project services (`TreeCopyHandler`, `IndentHelper`, `PomModel`).

To run auto-correct tests successfully, you must register these mocks and stub services on the test environment context before running `lint`:

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
