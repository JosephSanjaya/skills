---
name: dagger-hilt-expert
description: Expert guidance for Dagger and Hilt dependency injection in Android. Use when implementing DI, creating modules, configuring scopes, optimizing performance, testing with Hilt, setting up multi-module architecture, using assisted injection, or debugging DI issues. Triggers on "dagger", "hilt", "dependency injection", "@Module", "@Inject", "@Provides", "@Binds", "@Singleton", "@InstallIn", "@HiltAndroidApp", "@AndroidEntryPoint", "@HiltViewModel", "@AssistedInject", "DI setup", "module organization", "scope management", "Hilt testing", "@TestInstallIn", "@BindValue", or when working with Android DI architecture.
---

# Dagger & Hilt Expert

Expert guidance for professional Dagger and Hilt dependency injection in Android applications using KSP and modern best practices.

<instructions>
Provide precise, compile-time safe, and high-performance dependency injection advice. When assisting developers with Hilt, prioritize constructor injection, compile-time safety, proper scoping, and optimized test builds.
</instructions>

<rules>
## Core Principles

1. **Constructor Injection First**: Prefer `@Inject constructor` over modules when possible.
2. **@Binds Over @Provides**: Use `@Binds` for interface bindings to optimize class generation and startup.
3. **Narrow Scoping**: Only scope when necessary (state, expensive creation, synchronization). Feature-specific dependencies must not be `@Singleton`.
4. **Single-Purpose Modules**: Keep modules focused on one functional area (<10 providers).
5. **Lazy by Default**: Use `Lazy<T>` for non-critical startup dependencies to prevent app cold-start lag.

## Version and Gradle Configuration

Hilt projects should use Kotlin Symbol Processing (KSP) and the latest stable Hilt version (currently `2.59.2`).

```kotlin
// build.gradle.kts (Module level)
plugins {
    id("com.google.devtools.ksp")
    id("com.google.dagger.hilt.android")
}

dependencies {
    implementation("com.google.dagger:hilt-android:2.59.2")
    ksp("com.google.dagger:hilt-compiler:2.59.2")
    
    // For tests
    testImplementation("com.google.dagger:hilt-android-testing:2.59.2")
    kspTest("com.google.dagger:hilt-compiler:2.59.2")
    androidTestImplementation("com.google.dagger:hilt-android-testing:2.59.2")
    kspAndroidTest("com.google.dagger:hilt-compiler:2.59.2")
}
```

## Quick Reference

### Scope Selection

```
SingletonComponent (Annotation: @Singleton)
  ↓ (survives config changes)
ActivityRetainedComponent (Annotation: @ActivityRetainedScoped)
  ↓ (per ViewModel)
ViewModelComponent (Annotation: @ViewModelScoped)
  ↓ (per Activity)
ActivityComponent (Annotation: @ActivityScoped)
  ↓ (per Fragment)
FragmentComponent (Annotation: @FragmentScoped)
```

Use the narrowest scope possible. Do not scope stateless/cheap objects.

### Provision Method Selection Decision Tree

```
Do you own the class constructor?
├─ YES → Is it an interface binding?
│   ├─ YES → Use @Binds on an interface module
│   └─ NO → Use @Inject constructor on the class
└─ NO → Use @Provides on a static object/companion module
```

## Common Patterns

### Pattern: Network Module (Static @Provides)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideOkHttp(): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .build()
    
    @Provides
    @Singleton
    fun provideRetrofit(okHttp: OkHttpClient): Retrofit = Retrofit.Builder()
        .client(okHttp)
        .baseUrl("https://api.example.com")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
```

### Pattern: Repository Binding (@Binds)
```kotlin
interface UserRepository {
    suspend fun getUser(id: String): User
}

class UserRepositoryImpl @Inject constructor(
    private val api: UserApi,
    private val cache: UserCache
) : UserRepository {
    override suspend fun getUser(id: String): User =
        cache.get(id) ?: api.fetchUser(id).also { cache.put(id, it) }
}

@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {
    @Binds
    @Singleton
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
```

### Pattern: Lazy Initialization
```kotlin
@HiltAndroidApp
class MyApplication : Application() {
    @Inject lateinit var analytics: Lazy<Analytics>
    @Inject lateinit var crashReporter: Lazy<CrashReporter>
    
    override fun onCreate() {
        super.onCreate()
        crashReporter.get().initialize() // Critical only
        
        // Defer non-critical startup dependency to background thread
        CoroutineScope(Dispatchers.Default).launch {
            analytics.get().initialize()
        }
    }
}
```

### Pattern: Assisted Injection
```kotlin
class DetailViewModel @AssistedInject constructor(
    private val repository: Repository,
    @Assisted private val itemId: String
) : ViewModel() {
    @AssistedFactory
    interface Factory {
        fun create(itemId: String): DetailViewModel
    }
}

// Usage in Fragment
@AndroidEntryPoint
class DetailFragment : Fragment() {
    @Inject lateinit var factory: DetailViewModel.Factory
    
    private val viewModel by lazy {
        factory.create(requireArguments().getString("itemId")!!)
    }
}
```

### Pattern: WorkManager Custom Initialization
WorkManager requires custom initialization with `HiltWorkerFactory` to inject dependencies into `@HiltWorker` classes.
You MUST implement `Configuration.Provider` on the `Application` and disable the default WorkManagerInitializer in the manifest.

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val repository: SyncRepository
) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result = try {
        repository.sync()
        Result.success()
    } catch (e: Exception) {
        Result.retry()
    }
}
```

## Anti-Patterns to Avoid

### ❌ Monolithic Module
Keep modules single-purpose. Split large modules (e.g., `AppModule`) into `NetworkModule`, `DatabaseModule`, `AnalyticsModule`.

### ❌ Feature-Specific Singleton
Do not put feature-specific state (e.g. `OnboardingManager`) in `@Singleton` as it causes memory leaks. Use `@ActivityScoped` or `@ViewModelScoped`.

### ❌ Non-Static @Provides
```kotlin
@Module
class NetworkModule { // ❌ Class causes instance overhead
    @Provides fun provideGson(): Gson = Gson()
}
```
**Fix**: Use `object` and `@Provides` or `interface` and `@Binds`.

### ❌ @Provides for Simple Binding
```kotlin
@Provides fun provideRepo(impl: RepositoryImpl): Repository = impl // ❌ Inefficient
```
**Fix**: Use `@Binds` on an `interface` module.

## Detailed References
For deep dives into architectural setups and patterns, read:
- **[module-organization.md](references/module-organization.md)**: Single-purpose modules, visibility patterns, multi-module architecture, internal module trick.
- **[scoping-strategies.md](references/scoping-strategies.md)**: Component hierarchy, scope selection, lifecycle management, memory optimization.
- **[provides-vs-binds.md](references/provides-vs-binds.md)**: Performance comparison, when to use each, static vs instance methods, qualifiers.
- **[testing-patterns.md](references/testing-patterns.md)**: @TestInstallIn, @BindValue, @UninstallModules, fakes vs mocks, build optimization.
- **[performance-optimization.md](references/performance-optimization.md)**: Lazy injection, startup profiling, async initialization, memory management.
- **[assisted-injection.md](references/assisted-injection.md)**: Runtime parameters, WorkManager, SavedStateHandle, factory patterns.

## Scripts
- **analyze_modules.py**: Detects monolithic modules, non-static `@Provides`, and incorrect binding usage.
  `python scripts/analyze_modules.py <path_to_module>`
- **generate_module_template.sh**: Generates template for provides/binds modules.
  `./scripts/generate_module_template.sh <name> <component> <type>`

</rules>

<constraints>
- Developers **must** always recommend Constructor Injection over modules, unless dependencies are interfaces or external classes.
- You **should** never scope stateless dependencies. Explain that scoping only introduces DoubleCheck overhead.
- WorkManager Hilt integration **requires** implementing `Configuration.Provider` on the custom Hilt `Application` class and disabling the default WorkManager initializer via `AndroidManifest.xml` (otherwise, a crash will occur).
- For test environments, you **must** emphasize the build performance impact of `@UninstallModules` and recommend `@TestInstallIn` for global replacements to optimize build times.
- If the session gets long or slow, suggest `/clear` or `/compact` to prevent context decay.
</constraints>
