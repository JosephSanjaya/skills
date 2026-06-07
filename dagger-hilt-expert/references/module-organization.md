# Module Organization Best Practices

## Single-Purpose Module Pattern

Each Dagger/Hilt module should be responsible for a cohesive functional unit.

### Anti-Pattern: Monolithic Module
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides fun provideRetrofit(): Retrofit = ...
    @Provides fun provideOkHttp(): OkHttpClient = ...
    @Provides fun provideDatabase(): AppDatabase = ...
    @Provides fun provideLogger(): Logger = ...
    @Provides fun provideAnalytics(): Analytics = ...
    // 50+ more unrelated providers...
}
```

**Problems:**
- Any change forces re-evaluation of entire module
- Tests requiring one binding carry weight of all dependencies
- @TestInstallIn must replace entire module even for single binding

### Best Practice: Granular Modules
```kotlin
// Network module
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideRetrofit(okHttp: OkHttpClient): Retrofit = 
        Retrofit.Builder()
            .client(okHttp)
            .baseUrl("https://api.example.com")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    
    @Provides
    @Singleton
    fun provideOkHttp(): OkHttpClient = 
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .build()
}

// Database module
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .build()
    
    @Provides
    fun provideUserDao(db: AppDatabase): UserDao = db.userDao()
}

// Analytics module
@Module
@InstallIn(SingletonComponent::class)
object AnalyticsModule {
    @Provides
    @Singleton
    fun provideAnalytics(@ApplicationContext context: Context): Analytics =
        FirebaseAnalytics.getInstance(context)
}
```

## Module Visibility and Encapsulation

### Internal Module Pattern

Use when you want to hide implementation details within a Gradle module:

```kotlin
// Public interface (api module or public in feature module)
interface UserRepository {
    suspend fun getUser(id: String): User
}

// Internal implementation (same module)
internal class UserRepositoryImpl @Inject constructor(
    private val api: UserApi,
    private val cache: UserCache
) : UserRepository {
    override suspend fun getUser(id: String): User {
        return cache.get(id) ?: api.fetchUser(id).also { cache.put(id, it) }
    }
}

// Internal Dagger module
@Module
@InstallIn(SingletonComponent::class)
internal interface UserRepositoryBindings {
    @Binds
    @Singleton
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}

// Public module that includes the internal one
@Module(includes = [UserRepositoryBindings::class])
@InstallIn(SingletonComponent::class)
object UserModule
```

This allows `UserModule` to be referenced in the app module without exposing `UserRepositoryImpl`.

## Multi-Module Architecture Patterns

### Static Multi-Module Setup

```
app/
  ├── build.gradle.kts (implementation(project(":feature:login")))
  └── Application.kt (@HiltAndroidApp)

feature/
  └── login/
      ├── build.gradle.kts (implementation(project(":core:network")))
      └── LoginModule.kt (@InstallIn)

core/
  ├── network/
  │   └── NetworkModule.kt (@InstallIn(SingletonComponent::class))
  └── database/
      └── DatabaseModule.kt (@InstallIn(SingletonComponent::class))
```

**Key requirement:** All Hilt modules must be in transitive dependencies of the app module.

### Classpath Aggregation for Deep Hierarchies

```kotlin
// build.gradle.kts (app module)
hilt {
    enableAggregatingTask = true
}
```

Use when you have deeply nested module dependencies and encounter "missing binding" errors.

## Module Organization by Layer

### Domain Layer Modules
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {
    @Binds
    @Singleton
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
    
    @Binds
    @Singleton
    fun bindProductRepository(impl: ProductRepositoryImpl): ProductRepository
}
```

### Data Layer Modules
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface DataSourceModule {
    @Binds
    fun bindRemoteDataSource(impl: RemoteDataSourceImpl): RemoteDataSource
    
    @Binds
    fun bindLocalDataSource(impl: LocalDataSourceImpl): LocalDataSource
}
```

### Presentation Layer Modules
```kotlin
@Module
@InstallIn(ViewModelComponent::class)
interface UseCaseModule {
    @Binds
    fun bindLoginUseCase(impl: LoginUseCaseImpl): LoginUseCase
}
```

## Conditional Module Installation

### Feature Flag Pattern
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object FeatureModule {
    @Provides
    @Singleton
    fun provideFeatureManager(
        remoteConfig: RemoteConfig
    ): FeatureManager = FeatureManagerImpl(remoteConfig)
}

// In feature code
class FeatureViewModel @Inject constructor(
    private val featureManager: FeatureManager
) : ViewModel() {
    val isFeatureEnabled = featureManager.isEnabled("new_checkout")
}
```

### Build Variant Specific Modules
```kotlin
// src/debug/kotlin/DebugModule.kt
@Module
@InstallIn(SingletonComponent::class)
object DebugModule {
    @Provides
    @Singleton
    fun provideDebugTools(): DebugTools = DebugToolsImpl()
}

// src/release/kotlin/ReleaseModule.kt
@Module
@InstallIn(SingletonComponent::class)
object ReleaseModule {
    @Provides
    @Singleton
    fun provideDebugTools(): DebugTools = NoOpDebugTools()
}
```
