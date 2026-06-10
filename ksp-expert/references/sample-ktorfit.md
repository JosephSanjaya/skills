# Ktorfit Reference Implementation

Terse KSP2 processor implementation sample. Based on Ktorfit project structure.

## 1. Processor Provider

```kotlin
package de.jensklingenberg.ktorfit

import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider

class KtorfitProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        KtorfitProcessor(
            env = environment,
            ktorfitOptions = KtorfitOptions(environment.options)
        )
}
```

## 2. Processor Implementation

```kotlin
package de.jensklingenberg.ktorfit

import com.google.devtools.ksp.closestClassDeclaration
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSFunctionDeclaration

class KtorfitProcessor(
    private val env: SymbolProcessorEnvironment,
    private val ktorfitOptions: KtorfitOptions
) : SymbolProcessor {
    private var invoked = false

    override fun process(resolver: Resolver): List<KSAnnotated> {
        if (invoked) return emptyList()
        invoked = true

        val annotatedFunctions = getAnnotatedFunctions(resolver)
        val groupedClasses = annotatedFunctions
            .groupBy { it.closestClassDeclaration() }
            .mapNotNull { (classDec) ->
                classDec?.toClassData(KtorfitLogger(env.logger))
            }

        // Generate files
        generateImplClass(groupedClasses, env.codeGenerator, resolver, ktorfitOptions)

        return emptyList()
    }

    private fun getAnnotatedFunctions(resolver: Resolver): List<KSFunctionDeclaration> {
        val annotations = listOf("GET", "POST", "PUT", "DELETE", "PATCH", "HTTP")
        return annotations.flatMap { annotation ->
            resolver.getSymbolsWithAnnotation("de.jensklingenberg.ktorfit.http.$annotation")
        }.filterIsInstance<KSFunctionDeclaration>()
    }
}
```

## 3. Code Generation (Isolating Dependencies)

```kotlin
package de.jensklingenberg.ktorfit.generator

import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.Dependencies
import com.google.devtools.ksp.processing.Resolver
import de.jensklingenberg.ktorfit.KtorfitOptions
import de.jensklingenberg.ktorfit.model.ClassData
import java.io.OutputStreamWriter

fun generateImplClass(
    classDataList: List<ClassData>,
    codeGenerator: CodeGenerator,
    resolver: Resolver,
    ktorfitOptions: KtorfitOptions
) {
    classDataList.forEach { classData ->
        val fileSource = classData.generateSource(resolver, ktorfitOptions)
        val fileName = classData.implName
        val packageName = classData.packageName
        val sourceFile = classData.ksFile

        // Write isolating output: only invalidates if containing source file changes
        codeGenerator.createNewFile(
            dependencies = Dependencies(aggregating = false, sourceFile),
            packageName = packageName,
            fileName = fileName,
            extensionName = "kt"
        ).use { output ->
            OutputStreamWriter(output).use { writer ->
                writer.write(fileSource)
            }
        }
    }
}
```
