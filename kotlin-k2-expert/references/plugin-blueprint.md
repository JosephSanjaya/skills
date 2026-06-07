# K2 Plugin Blueprint — Full Module Setup

Read when: setting up new K2 compiler plugin, wiring Gradle plugin, configuring service files, implementing CommandLineProcessor.

## Project Structure

```
my-k2-plugin/
├── build.gradle.kts                    # Root
├── settings.gradle.kts
├── gradle/libs.versions.toml
├── annotations/                        # Thin runtime (no compiler deps)
│   ├── build.gradle.kts
│   └── src/commonMain/kotlin/com/example/annotations/
│       └── MyAnnotation.kt
├── compiler-plugin/                    # FIR + IR + registrar
│   ├── build.gradle.kts
│   ├── src/main/kotlin/com/example/plugin/
│   │   ├── MyPluginRegistrar.kt
│   │   ├── MyCommandLineProcessor.kt
│   │   ├── MyConfigurationKeys.kt
│   │   ├── fir/
│   │   │   ├── MyFirRegistrar.kt
│   │   │   ├── MyFirGenerator.kt
│   │   │   ├── MyFirChecker.kt
│   │   │   └── MySessionComponent.kt
│   │   └── ir/
│   │       ├── MyIrExtension.kt
│   │       ├── MyStubGenerator.kt
│   │       └── MyBodyGenerator.kt
│   ├── src/main/resources/META-INF/services/
│   │   ├── org.jetbrains.kotlin.compiler.plugin.CompilerPluginRegistrar
│   │   └── org.jetbrains.kotlin.compiler.plugin.CommandLineProcessor
│   └── testData/
│       ├── box/
│       └── diagnostics/
└── gradle-plugin/                      # Gradle integration
    ├── build.gradle.kts
    └── src/main/kotlin/com/example/gradle/
        ├── MyGradlePlugin.kt
        └── MyExtension.kt
```

## Service Files

### `META-INF/services/org.jetbrains.kotlin.compiler.plugin.CompilerPluginRegistrar`
```
com.example.plugin.MyPluginRegistrar
```

### `META-INF/services/org.jetbrains.kotlin.compiler.plugin.CommandLineProcessor`
```
com.example.plugin.MyCommandLineProcessor
```

## CommandLineProcessor

```kotlin
package com.example.plugin

import org.jetbrains.kotlin.compiler.plugin.*
import org.jetbrains.kotlin.config.*

object MyConfigurationKeys {
    val ENABLED = CompilerConfigurationKey<Boolean>("enable processing")
    val LOG_LEVEL = CompilerConfigurationKey<String>("log verbosity")
    val TARGET_ANNOTATION = CompilerConfigurationKey<String>("annotation FQN")
}

class MyCommandLineProcessor : CommandLineProcessor {
    override val pluginId = "com.example.my-plugin"

    override val pluginOptions: Collection<AbstractCliOption> = listOf(
        CliOption("enabled", "<true|false>", "Enable plugin", required = false),
        CliOption("logLevel", "<none|user|debug>", "Log verbosity", required = false),
        CliOption("targetAnnotation", "<fqn>", "Annotation to process", required = false),
    )

    override fun processOption(option: AbstractCliOption, value: String, config: CompilerConfiguration) {
        when (option.optionName) {
            "enabled" -> config.put(MyConfigurationKeys.ENABLED, value.toBooleanStrict())
            "logLevel" -> config.put(MyConfigurationKeys.LOG_LEVEL, value)
            "targetAnnotation" -> config.put(MyConfigurationKeys.TARGET_ANNOTATION, value)
        }
    }
}
```

## CompilerPluginRegistrar

```kotlin
package com.example.plugin

import org.jetbrains.kotlin.backend.common.extensions.IrGenerationExtension
import org.jetbrains.kotlin.cli.common.messages.MessageCollector
import org.jetbrains.kotlin.compiler.plugin.CompilerPluginRegistrar
import org.jetbrains.kotlin.config.CommonConfigurationKeys
import org.jetbrains.kotlin.config.CompilerConfiguration
import org.jetbrains.kotlin.fir.extensions.FirExtensionRegistrarAdapter

class MyPluginRegistrar : CompilerPluginRegistrar() {
    override val supportsK2 = true
    override val pluginId = "com.example.my-plugin" // Must match CLI processor + Gradle

    override fun ExtensionStorage.registerExtensions(config: CompilerConfiguration) {
        val enabled = config.get(MyConfigurationKeys.ENABLED, true)
        if (!enabled) return

        val msgCollector = config.get(CommonConfigurationKeys.MESSAGE_COLLECTOR_KEY, MessageCollector.NONE)
        val lookupTracker = config.get(CommonConfigurationKeys.LOOKUP_TRACKER)
        val expectActualTracker = config.get(CommonConfigurationKeys.EXPECT_ACTUAL_TRACKER)

        // FIR (frontend — signatures, checkers)
        FirExtensionRegistrarAdapter.registerExtension(MyFirRegistrar())
        // IR (backend — bodies, transforms)
        IrGenerationExtension.registerExtension(MyIrExtension(msgCollector, lookupTracker))
    }
}
```

## FirExtensionRegistrar

```kotlin
package com.example.plugin.fir

import org.jetbrains.kotlin.fir.extensions.FirExtensionRegistrar

class MyFirRegistrar : FirExtensionRegistrar() {
    override fun ExtensionRegistrarContext.configurePlugin() {
        +::MyFirGenerator       // FirDeclarationGenerationExtension
        +::MyFirChecker         // FirAdditionalCheckersExtension
    }
}
```

## FirDeclarationGenerationExtension

```kotlin
package com.example.plugin.fir

import org.jetbrains.kotlin.fir.FirSession
import org.jetbrains.kotlin.fir.extensions.FirDeclarationGenerationExtension
import org.jetbrains.kotlin.fir.extensions.MemberGenerationContext
import org.jetbrains.kotlin.fir.symbols.impl.*
import org.jetbrains.kotlin.name.*

class MyFirGenerator(session: FirSession) : FirDeclarationGenerationExtension(session) {

    object Key : org.jetbrains.kotlin.GeneratedDeclarationKey()

    override fun getCallableNamesForClass(classSymbol: FirClassSymbol<*>): Set<Name> {
        // Only generate for annotated classes
        if (!classSymbol.hasAnnotation(MY_ANNOTATION_FQN)) return emptySet()
        return setOf(Name.identifier("generatedMethod"))
    }

    override fun generateFunctions(
        callableId: CallableId,
        context: MemberGenerationContext?
    ): List<FirNamedFunctionSymbol> {
        if (callableId.callableName.asString() != "generatedMethod") return emptyList()
        if (context == null) return emptyList()

        // Build signature only — NO body. Body filled in IR.
        // Use Key as origin for Fir2Ir symbol mapping.
        val functionSymbol = FirSimpleFunctionSymbol(callableId)
        // ... configure return type, parameters, visibility using FirDeclarationBuilder
        return listOf(functionSymbol)
    }

    companion object {
        val MY_ANNOTATION_FQN = ClassId.topLevel(FqName("com.example.annotations.AutoGenerate"))
    }
}
```

## FirAdditionalCheckersExtension

```kotlin
package com.example.plugin.fir

import org.jetbrains.kotlin.fir.FirSession
import org.jetbrains.kotlin.fir.analysis.checkers.declaration.*
import org.jetbrains.kotlin.fir.analysis.extensions.FirAdditionalCheckersExtension

class MyFirChecker(session: FirSession) : FirAdditionalCheckersExtension(session) {
    override val declarationCheckers = object : DeclarationCheckers() {
        override val classCheckers: Set<FirClassChecker> = setOf(MyClassChecker)
    }
}

object MyClassChecker : FirClassChecker() {
    override fun check(declaration: FirClass, context: CheckerContext, reporter: DiagnosticReporter) {
        // Validate annotated classes meet requirements
        // reporter.reportOn(source, MyErrors.INVALID_USAGE, context)
    }
}
```

## FirExtensionSessionComponent (Caching)

```kotlin
package com.example.plugin.fir

import org.jetbrains.kotlin.fir.FirSession
import org.jetbrains.kotlin.fir.extensions.FirExtensionSessionComponent

class MySessionComponent(session: FirSession) : FirExtensionSessionComponent(session) {
    // Lazy-init classpath scan — persists across incremental daemon builds
    private val annotatedClasses: Set<ClassId> by lazy {
        scanClasspathForAnnotation(session)
    }

    fun getAnnotatedClasses(): Set<ClassId> = annotatedClasses

    private fun scanClasspathForAnnotation(session: FirSession): Set<ClassId> {
        // Obtain classpath from CompilerConfiguration in registration phase
        // Use ClassGraph or manual JAR scanning
        // Cache results — FirSession persists across IC steps in daemon
        return emptySet()
    }
}
```

## IrGenerationExtension (Two-Pass)

```kotlin
package com.example.plugin.ir

import org.jetbrains.kotlin.backend.common.extensions.*
import org.jetbrains.kotlin.cli.common.messages.MessageCollector
import org.jetbrains.kotlin.incremental.components.LookupTracker
import org.jetbrains.kotlin.ir.declarations.IrModuleFragment

class MyIrExtension(
    private val messageCollector: MessageCollector,
    private val lookupTracker: LookupTracker?,
) : IrGenerationExtension {
    override fun generate(moduleFragment: IrModuleFragment, pluginContext: IrPluginContext) {
        // Pass 1: Stubs — register ALL class/function declarations with empty bodies
        val stubGen = MyStubGenerator(pluginContext)
        moduleFragment.files.forEach { stubGen.runOnFileInOrder(it) }

        // Pass 2: Bodies — fill implementations, all symbols now resolvable
        val bodyGen = MyBodyGenerator(pluginContext)
        moduleFragment.files.forEach { bodyGen.runOnFileInOrder(it) }
    }
}
```

## Gradle Plugin

```kotlin
package com.example.gradle

import org.gradle.api.Project
import org.gradle.api.provider.Provider
import org.jetbrains.kotlin.gradle.plugin.*

class MyGradlePlugin : KotlinCompilerPluginSupportPlugin {
    override fun isApplicable(kotlinCompilation: KotlinCompilation<*>) = true
    override fun getCompilerPluginId() = "com.example.my-plugin"
    override fun getPluginArtifact() = SubpluginArtifact("com.example", "compiler-plugin", "1.0.0")

    override fun apply(target: Project) {
        target.extensions.create("myPlugin", MyExtension::class.java)
    }

    override fun applyToCompilation(c: KotlinCompilation<*>): Provider<List<SubpluginOption>> {
        val project = c.target.project
        val ext = project.extensions.getByType(MyExtension::class.java)
        return project.provider {
            listOf(
                SubpluginOption("enabled", ext.enabled.get().toString()),
                SubpluginOption("logLevel", ext.logLevel.get()),
            )
        }
    }
}

open class MyExtension(objects: org.gradle.api.model.ObjectFactory) {
    val enabled = objects.property(Boolean::class.java).convention(true)
    val logLevel = objects.property(String::class.java).convention("none")
}
```

## Build Configuration

### compiler-plugin/build.gradle.kts
```kotlin
plugins { kotlin("jvm") }

dependencies {
    compileOnly("org.jetbrains.kotlin:kotlin-compiler-embeddable")
    testImplementation("org.jetbrains.kotlin:kotlin-compiler-internal-test-framework")
    testImplementation(kotlin("test"))
    testRuntimeOnly("org.jetbrains.kotlin:kotlin-test")
    testRuntimeOnly("org.jetbrains.kotlin:kotlin-scripting-compiler")
    testRuntimeOnly("org.jetbrains.kotlin:kotlin-annotations-jvm")
    testImplementation(project(":annotations"))
}

kotlin {
    compilerOptions {
        apiVersion.set(org.jetbrains.kotlin.gradle.dsl.KotlinVersion.KOTLIN_2_4)
        languageVersion.set(org.jetbrains.kotlin.gradle.dsl.KotlinVersion.KOTLIN_2_4)
    }
}
```

### gradle/libs.versions.toml
```toml
[versions]
kotlin = "2.4.0"

[libraries]
kotlin-compiler = { module = "org.jetbrains.kotlin:kotlin-compiler-embeddable", version.ref = "kotlin" }
kotlin-test-framework = { module = "org.jetbrains.kotlin:kotlin-compiler-internal-test-framework", version.ref = "kotlin" }

[plugins]
kotlin-jvm = { id = "org.jetbrains.kotlin.jvm", version.ref = "kotlin" }
```

### annotations/build.gradle.kts
```kotlin
plugins { kotlin("multiplatform") }

kotlin {
    jvm(); js(IR) { browser(); nodejs() }
    sourceSets { commonMain { /* zero deps */ } }
}
```

### Annotation example
```kotlin
package com.example.annotations

@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.BINARY)
annotation class AutoGenerate(val generateFactory: Boolean = false)
```
