# @Provides vs @Binds: Performance and Usage Patterns

## Decision Matrix

| Scenario | Use | Reason |
|----------|-----|--------|
| Own the constructor | `@Inject constructor` | Most efficient, no module needed |
| Interface → Implementation (own constructor) | `@Binds` | No module instantiation, cast-only |
| Third-party library | `@Provides` | No access to constructor |
| Complex initialization logic | `@Provides` | Need custom setup code |
| Multiple instances with different configs | `@Provides` with qualifiers | Need parameterization |

## Constructor Injection (Preferred)

### Pattern
```kotlin
class UserRepository @Inject constructor(
    private val api: UserApi,
    private val cache: UserCache
) {
    suspend fun getUser(id: String): User {
        return cache.get(id) ?: api.fetchUser(id)
    }
}

// No module needed! Dagger automatically knows how to create this.
```

### Generated Code
```java
public final class UserRepository_Factory implements Factory<UserRepository> {
    private final Provider<UserApi> apiProvider;
    private final Provider<UserCache> cacheProvider;
    
    @Override
    public UserRepository get() {
        return new UserRepository(apiProvider.get(), cacheProvider.get());
    }
}
```

**Efficiency:** Minimal overhead, direct instantiation.

## @Binds (Second Best)

### Pattern
```kotlin
interface UserRepository {
    suspend fun getUser(id: String): User
}

class UserRepositoryImpl @Inject constructor(
    private val api: UserApi,
    private val cache: UserCache
) : UserRepository {
    override suspend fun getUser(id: String): User {
        return cache.get(id) ?: api.fetchUser(id)
    }
}

@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {
    @Binds
    @Singleton
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
```

### Generated Code
```java
// No module instantiation needed!
public final class RepositoryModule_BindUserRepository implements Factory<UserRepository> {
    private final Provider<UserRepositoryImpl> implProvider;
    
    @Override
    public UserRepository get() {
        return implProvider.get();  // Simple cast
    }
}
```

**Efficiency:** Very low overhead, no module instance required.

### Requirements for @Binds
1. Must be an abstract method
2. Must be in an abstract class or interface
3. Return type must be assignable from parameter type
4. Must have exactly one parameter

## @Provides (When Necessary)

### Use Case 1: Third-Party Library
```kotlin
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
}
```

### Use Case 2: Complex Initialization
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
            .fallbackToDestructiveMigration()
            .build()
}
```

### Use Case 3: Conditional Logic
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object LoggerModule {
    @Provides
    @Singleton
    fun provideLogger(buildConfig: BuildConfig): Logger =
        if (buildConfig.isDebug) {
            DebugLogger()
        } else {
            ProductionLogger()
        }
}
```

## Static vs Instance @Provides

### Instance Method (Avoid)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
class NetworkModule {  // ❌ Class, not object
    
    @Provides
    fun provideGson(): Gson = GsonBuilder().create()
}
```

**Generated Code:**
```java
public final class NetworkModule_ProvideGsonFactory {
    private final NetworkModule module;  // ❌ Module instance stored
    
    public Gson get() {
        return module.provideGson();  // ❌ Instance method call
    }
}
```

**Problem:** Dagger must instantiate `NetworkModule` to call the provider method.

### Static Method (Preferred)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {  // ✅ Object = static in Java
    
    @Provides
    fun provideGson(): Gson = GsonBuilder().create()
}
```

**Generated Code:**
```java
public final class NetworkModule_ProvideGsonFactory {
    public static Gson get() {  // ✅ Static method
        return NetworkModule.INSTANCE.provideGson();
    }
}
```

**Benefit:** No module instantiation overhead.

### Explicit Static in Java
```java
@Module
@InstallIn(SingletonComponent.class)
public abstract class NetworkModule {
    
    @Provides
    static Gson provideGson() {  // ✅ Explicit static
        return new GsonBuilder().create();
    }
}
```

## Combining @Binds and @Provides

### Problem: Can't Mix in Same Module
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {
    @Binds
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
    
    // ❌ Error: @Provides not allowed in interface
    @Provides
    fun provideApiKey(): String = "secret-key"
}
```

### Solution 1: Separate Modules
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface RepositoryBindings {
    @Binds
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}

@Module
@InstallIn(SingletonComponent::class)
object RepositoryProviders {
    @Provides
    fun provideApiKey(): String = "secret-key"
}
```

### Solution 2: Companion Object
```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    
    @Binds
    abstract fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
    
    companion object {
        @Provides
        fun provideApiKey(): String = "secret-key"
    }
}
```

## Qualifiers with @Binds and @Provides

### @Binds with Qualifier
```kotlin
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class LocalDataSource

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class RemoteDataSource

@Module
@InstallIn(SingletonComponent::class)
interface DataSourceModule {
    @Binds
    @LocalDataSource
    fun bindLocalDataSource(impl: LocalDataSourceImpl): DataSource
    
    @Binds
    @RemoteDataSource
    fun bindRemoteDataSource(impl: RemoteDataSourceImpl): DataSource
}

class UserRepository @Inject constructor(
    @LocalDataSource private val local: DataSource,
    @RemoteDataSource private val remote: DataSource
)
```

### @Provides with Qualifier
```kotlin
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class AuthInterceptor

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class LoggingInterceptor

@Module
@InstallIn(SingletonComponent::class)
object InterceptorModule {
    @Provides
    @AuthInterceptor
    fun provideAuthInterceptor(tokenManager: TokenManager): Interceptor =
        Interceptor { chain ->
            val request = chain.request().newBuilder()
                .addHeader("Authorization", "Bearer ${tokenManager.getToken()}")
                .build()
            chain.proceed(request)
        }
    
    @Provides
    @LoggingInterceptor
    fun provideLoggingInterceptor(): Interceptor =
        HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
}
```

## Performance Comparison

### Benchmark Results (Relative Cost)
```
Constructor Injection:     1.0x (baseline)
@Binds:                    1.1x (minimal cast overhead)
@Provides (static):        1.5x (factory + method call)
@Provides (instance):      2.0x (module instantiation + factory + method call)
```

## Migration Path: Instance → Static → @Binds → Constructor

### Step 1: Instance @Provides (Starting Point)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
class RepositoryModule {
    @Provides
    fun provideUserRepository(api: UserApi): UserRepository =
        UserRepositoryImpl(api)
}
```

### Step 2: Convert to Object (Static)
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {  // ✅ Now static
    @Provides
    fun provideUserRepository(api: UserApi): UserRepository =
        UserRepositoryImpl(api)
}
```

### Step 3: Add @Inject Constructor
```kotlin
class UserRepositoryImpl @Inject constructor(
    private val api: UserApi
) : UserRepository
```

### Step 4: Convert to @Binds
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {  // ✅ Now interface with @Binds
    @Binds
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
```

### Step 5: Remove Module if Possible
```kotlin
// If UserRepository is only used as concrete type, remove module entirely
class UserRepositoryImpl @Inject constructor(
    private val api: UserApi
) : UserRepository

// Inject directly
class UserViewModel @Inject constructor(
    private val repository: UserRepositoryImpl  // ✅ No module needed
)
```

## Common Mistakes

### Mistake 1: Using @Provides for Simple Interface Binding
```kotlin
// ❌ Bad
@Provides
fun provideUserRepository(impl: UserRepositoryImpl): UserRepository = impl

// ✅ Good
@Binds
fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
```

### Mistake 2: Non-Static @Provides
```kotlin
// ❌ Bad
@Module
@InstallIn(SingletonComponent::class)
class NetworkModule {
    @Provides
    fun provideGson(): Gson = GsonBuilder().create()
}

// ✅ Good
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    fun provideGson(): Gson = GsonBuilder().create()
}
```

### Mistake 3: Forgetting @Inject Constructor
```kotlin
// ❌ Bad: Need @Provides
class UserRepositoryImpl(private val api: UserApi) : UserRepository

// ✅ Good: Can use @Binds
class UserRepositoryImpl @Inject constructor(
    private val api: UserApi
) : UserRepository
```
