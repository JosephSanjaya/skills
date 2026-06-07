# Koin Multi-Module Patterns

## Local ComponentScan Boundary

The `@ComponentScan` annotation only scans classes compiled in the **current Gradle module**. It cannot inspect pre-compiled JARs, external libraries, or upstream Gradle modules.

## Cross-Module Assembly Root

To build a complete dependency graph, the aggregator or composition root (`app` module) must explicitly include all modular configurations:

```kotlin
@Module(includes = [
    NativeFrameworkModule::class,
    FeatureAModule::class,
    FeatureBModule::class,
])
@ComponentScan("com.architecture.presentation")
class ComposeAppModule

@KoinApplication(modules = [ComposeAppModule::class])
class ApplicationGraph
```

## Clean Architecture Boundaries using `@Provided`

In clean architectures, core domain modules define interfaces, and infrastructure/framework modules implement them. Because the domain module cannot depend on infrastructure compile-time dependencies, compiler validation (A2 check) inside the `:domain` module would fail due to missing concrete implementations.

Using `@Provided` instructs the compiler to skip A2 local validation for a parameter, deferring validation to the A3 phase (composition root):

```kotlin
// In `:domain` module:
@Factory
class FetchUserDataUseCase(
    @Provided private val remoteDataSource: RemoteDataSource,  // Deferred to A3
    @Provided private val localCache: UserCache,               // Deferred to A3
)
```

Without the `@Provided` annotation, compiling `:domain` would fail with: `Missing dependency: RemoteDataSource`.

## KMP: expect/actual Overrides (Last-Definition-Wins)

Use the expect/actual pattern to register platform-specific overrides:

```kotlin
// In commonMain (default implementation):
@Module
class FrameworkModule {
    @Single
    fun provideFileConverter(): PlatformFileConverter = CommonFileConverter()
}

// In commonMain (expect wrapper including default module):
@Module([FrameworkModule::class])
expect class NativeFrameworkModule()

// In androidMain (actual providing Android-specific override):
@Module
@ComponentScan("com.architecture.framework")
actual class NativeFrameworkModule {
    @Single
    fun provideFileConverter(): PlatformFileConverter = AndroidFileConverter()
}
```

Due to Koin's "last definition wins" resolution order, `AndroidFileConverter` overrides the `CommonFileConverter` definition on Android.

## Dynamic Feature Module Loading

For large features or on-demand feature modules (e.g. settings, onboarding, checkout), load modules dynamically to optimize memory consumption:

```kotlin
// Load feature module when entering the flow:
loadKoinModules(featurePaymentModule)

// Unload feature module on flow exit:
unloadKoinModules(featurePaymentModule)
```

## Testing Multi-Module Graphs

The compile-time checks (A2/A3/A4) ensure graph integrity, making legacy `checkModules()` / `verify()` unit tests obsolete. 

To mock or substitute components in unit tests, construct a programmatically-scoped test container:

```kotlin
val testModule = module {
    single<NetworkModule> { FakeNetworkModule() }
}

startKoin { 
    modules(AppModule.module(), testModule) 
}
```
