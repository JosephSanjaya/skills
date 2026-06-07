# Scoping Strategies and Lifecycle Management

## Hilt Component Hierarchy

```
SingletonComponent (@Singleton)
    ↓
ActivityRetainedComponent (@ActivityRetainedScoped)
    ↓
ViewModelComponent (@ViewModelScoped)
    ↓
ActivityComponent (@ActivityScoped)
    ↓
FragmentComponent (@FragmentScoped)
    ↓
ViewComponent (@ViewScoped)
    ↓
ViewWithFragmentComponent (@ViewScoped)
    ↓
ServiceComponent (@ServiceScoped)
```

## Scope Selection Decision Tree

```
Is the dependency truly global (network, database)?
├─ YES → @Singleton in SingletonComponent
└─ NO → Does it need to survive configuration changes?
    ├─ YES → Is it used in ViewModel?
    │   ├─ YES → @ActivityRetainedScoped in ActivityRetainedComponent
    │   └─ NO → @ActivityScoped in ActivityComponent
    └─ NO → Is it tied to a specific screen?
        ├─ Fragment → @FragmentScoped in FragmentComponent
        ├─ Activity → @ActivityScoped in ActivityComponent
        └─ ViewModel → @ViewModelScoped in ViewModelComponent
```

## Anti-Pattern: Singleton-by-Default

### Bad: Feature-Specific Singleton
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object OnboardingModule {
    @Provides
    @Singleton  // ❌ Lives forever!
    fun provideOnboardingRepository(
        api: OnboardingApi
    ): OnboardingRepository = OnboardingRepositoryImpl(api)
}
```

**Problem:** OnboardingRepository stays in memory even after onboarding is complete.

### Good: Activity-Scoped
```kotlin
@Module
@InstallIn(ActivityComponent::class)
object OnboardingModule {
    @Provides
    @ActivityScoped  // ✅ Cleaned up when activity finishes
    fun provideOnboardingRepository(
        api: OnboardingApi
    ): OnboardingRepository = OnboardingRepositoryImpl(api)
}

@AndroidEntryPoint
class OnboardingActivity : AppCompatActivity() {
    @Inject lateinit var repository: OnboardingRepository
}
```

## Proper Singleton Usage

### Valid Singleton: Network Client
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton  // ✅ Truly global, expensive to create
    fun provideOkHttpClient(): OkHttpClient =
        OkHttpClient.Builder()
            .connectionPool(ConnectionPool(5, 5, TimeUnit.MINUTES))
            .build()
}
```

### Valid Singleton: Database
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton  // ✅ Single source of truth
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .build()
}
```

## ActivityRetainedScoped for ViewModels

### Pattern: Repository Shared Across ViewModels
```kotlin
@Module
@InstallIn(ActivityRetainedComponent::class)
object CheckoutModule {
    @Provides
    @ActivityRetainedScoped  // ✅ Survives rotation, shared by all VMs in activity
    fun provideCheckoutRepository(
        api: CheckoutApi,
        cartManager: CartManager
    ): CheckoutRepository = CheckoutRepositoryImpl(api, cartManager)
}

@HiltViewModel
class CartViewModel @Inject constructor(
    private val repository: CheckoutRepository
) : ViewModel()

@HiltViewModel
class PaymentViewModel @Inject constructor(
    private val repository: CheckoutRepository  // Same instance as CartViewModel
) : ViewModel()
```

## ViewModelScoped for ViewModel-Specific Dependencies

```kotlin
@Module
@InstallIn(ViewModelComponent::class)
object UseCaseModule {
    @Provides
    @ViewModelScoped  // ✅ Tied to specific ViewModel lifecycle
    fun provideValidatePaymentUseCase(
        repository: CheckoutRepository
    ): ValidatePaymentUseCase = ValidatePaymentUseCaseImpl(repository)
}

@HiltViewModel
class PaymentViewModel @Inject constructor(
    private val validatePayment: ValidatePaymentUseCase
) : ViewModel()
```

## FragmentScoped Considerations

### Warning: Each Fragment Instance Gets Own Component
```kotlin
@Module
@InstallIn(FragmentComponent::class)
object ProductModule {
    @Provides
    @FragmentScoped
    fun provideProductCache(): ProductCache = ProductCacheImpl()
}

// ❌ Problem: Two instances of ProductListFragment = two ProductCache instances
class ProductListFragment : Fragment() {
    @Inject lateinit var cache: ProductCache
}
```

### Solution: Use ActivityScoped or ActivityRetainedScoped
```kotlin
@Module
@InstallIn(ActivityRetainedComponent::class)
object ProductModule {
    @Provides
    @ActivityRetainedScoped  // ✅ Shared across all fragments in activity
    fun provideProductCache(): ProductCache = ProductCacheImpl()
}
```

## Unscoped Dependencies

### When NOT to Scope
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface MapperModule {
    @Binds  // ✅ No scope - stateless, cheap to create
    fun bindUserMapper(impl: UserMapperImpl): UserMapper
}

data class UserMapperImpl @Inject constructor() : UserMapper {
    override fun map(dto: UserDto): User = User(
        id = dto.id,
        name = dto.name
    )
}
```

**Rule:** Only scope if:
1. Object has internal state that must be shared
2. Construction is expensive (network, database, heavy computation)
3. Synchronization is required

## Performance Cost of Scoping

### DoubleCheck Overhead
```kotlin
// Scoped binding generates:
public final class NetworkModule_ProvideOkHttpClientFactory {
    private static volatile Provider<OkHttpClient> instance;
    
    public static OkHttpClient get() {
        if (instance == null) {
            synchronized (NetworkModule_ProvideOkHttpClientFactory.class) {
                if (instance == null) {  // DoubleCheck
                    instance = NetworkModule.provideOkHttpClient();
                }
            }
        }
        return instance.get();
    }
}

// Unscoped binding generates:
public final class MapperModule_ProvideUserMapperFactory {
    public static UserMapper get() {
        return new UserMapperImpl();  // Direct instantiation
    }
}
```

## Lifecycle Hooks and Cleanup

### ActivityRetainedComponent Cleanup
```kotlin
// Hilt stores ActivityRetainedComponent in a ViewModel
internal class ActivityRetainedComponentViewModel : ViewModel() {
    val component: ActivityRetainedComponent = ...
    
    override fun onCleared() {
        // Called when Activity is finishing (not rotating)
        // All @ActivityRetainedScoped dependencies are eligible for GC
    }
}
```

### Manual Cleanup Pattern
```kotlin
interface Closeable {
    fun close()
}

class DatabaseConnection @Inject constructor() : Closeable {
    override fun close() {
        // Release resources
    }
}

@HiltViewModel
class DataViewModel @Inject constructor(
    private val connection: DatabaseConnection
) : ViewModel() {
    override fun onCleared() {
        connection.close()
    }
}
```

## Scope Validation Checklist

Before adding a scope annotation, verify:

- [ ] Does this object have mutable state that must be shared?
- [ ] Is construction expensive enough to justify caching?
- [ ] Is this the narrowest possible scope for the use case?
- [ ] Have I profiled to confirm the performance benefit?
- [ ] Will this cause memory leaks if the scope is too broad?

## Common Scoping Mistakes

### Mistake 1: Scoping Stateless Objects
```kotlin
// ❌ Bad
@Provides
@Singleton
fun provideJsonParser(): JsonParser = JsonParserImpl()

// ✅ Good
@Provides
fun provideJsonParser(): JsonParser = JsonParserImpl()
```

### Mistake 2: Wrong Scope for Use Case
```kotlin
// ❌ Bad: Login state in Singleton
@Provides
@Singleton
fun provideLoginManager(): LoginManager = LoginManagerImpl()

// ✅ Good: Login state in Activity
@Provides
@ActivityScoped
fun provideLoginManager(): LoginManager = LoginManagerImpl()
```

### Mistake 3: Leaking Activity Context
```kotlin
// ❌ Bad: Activity context in Singleton
@Provides
@Singleton
fun provideLocationManager(activity: Activity): LocationManager =
    activity.getSystemService(Context.LOCATION_SERVICE) as LocationManager

// ✅ Good: Use Application context
@Provides
@Singleton
fun provideLocationManager(@ApplicationContext context: Context): LocationManager =
    context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
```
