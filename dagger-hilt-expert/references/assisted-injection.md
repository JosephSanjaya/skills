# Assisted Injection Patterns

## Problem: Runtime Parameters + DI Dependencies

Some classes need both:
1. Dependencies from the DI graph (repositories, APIs)
2. Runtime parameters (user ID, navigation args, WorkManager params)

## Solution: @AssistedInject

### Basic Pattern

```kotlin
class UserDetailViewModel @AssistedInject constructor(
    private val repository: UserRepository,  // From DI graph
    @Assisted private val userId: String     // Runtime parameter
) : ViewModel() {
    
    @AssistedFactory
    interface Factory {
        fun create(userId: String): UserDetailViewModel
    }
    
    val user: StateFlow<User?> = flow {
        emit(repository.getUser(userId))
    }.stateIn(viewModelScope, SharingStarted.Lazily, null)
}
```

### Usage in Fragment

```kotlin
@AndroidEntryPoint
class UserDetailFragment : Fragment() {
    
    @Inject
    lateinit var viewModelFactory: UserDetailViewModel.Factory
    
    private val viewModel: UserDetailViewModel by lazy {
        val userId = requireArguments().getString("userId")!!
        viewModelFactory.create(userId)
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.user.collect { user ->
                // Update UI
            }
        }
    }
}
```

## WorkManager Integration

### Pattern: Worker with Assisted Injection

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted private val context: Context,        // From WorkManager
    @Assisted private val params: WorkerParameters, // From WorkManager
    private val repository: SyncRepository,         // From DI graph
    private val analytics: Analytics                // From DI graph
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        return try {
            val syncType = params.inputData.getString("sync_type") ?: "full"
            
            repository.sync(syncType)
            analytics.logEvent("sync_completed", mapOf("type" to syncType))
            
            Result.success()
        } catch (e: Exception) {
            analytics.logEvent("sync_failed", mapOf("error" to e.message))
            Result.retry()
        }
    }
}

// Scheduling the worker
class SyncScheduler @Inject constructor(
    @ApplicationContext private val context: Context
) {
    fun scheduleSyncWork(syncType: String) {
        val data = Data.Builder()
            .putString("sync_type", syncType)
            .build()
        
        val request = OneTimeWorkRequestBuilder<SyncWorker>()
            .setInputData(data)
            .build()
        
        WorkManager.getInstance(context).enqueue(request)
    }
}
```

### Custom Application Setup for WorkManager

WorkManager's default auto-initializer must be disabled and replaced so that Hilt can inject dependencies into `@HiltWorker` classes. Implement `Configuration.Provider` on your `Application` class:

```kotlin
import android.app.Application
import androidx.work.Configuration
import androidx.work.HiltWorkerFactory
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class MyApplication : Application(), Configuration.Provider {

    @Inject lateinit var workerFactory: HiltWorkerFactory

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
}
```

### Disable Default WorkManager Initializer

You MUST disable the default initializer in your `AndroidManifest.xml` so that WorkManager uses your custom application configuration rather than trying to instantiate workers using the default constructor (which causes a `NoSuchMethodException` crash):

```xml
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    android:exported="false"
    tools:node="merge">
    
    <!-- This removes the default WorkManagerInitializer -->
    <meta-data
        android:name="androidx.work.WorkManagerInitializer"
        android:value="androidx.startup"
        tools:node="remove" />
</provider>
```


## SavedStateHandle Integration

### Pattern: ViewModel with Navigation Args

```kotlin
@HiltViewModel
class ProductDetailViewModel @Inject constructor(
    private val repository: ProductRepository,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    
    private val productId: String = savedStateHandle["productId"]
        ?: throw IllegalArgumentException("productId required")
    
    val product: StateFlow<Product?> = flow {
        emit(repository.getProduct(productId))
    }.stateIn(viewModelScope, SharingStarted.Lazily, null)
}

// Navigation setup (Compose)
@Composable
fun ProductDetailScreen(
    viewModel: ProductDetailViewModel = hiltViewModel()
) {
    val product by viewModel.product.collectAsState()
    
    product?.let {
        // Display product
    }
}
```

## Multiple Assisted Parameters

### Pattern: Complex Factory

```kotlin
class OrderProcessor @AssistedInject constructor(
    private val paymentService: PaymentService,     // DI
    private val shippingService: ShippingService,   // DI
    @Assisted private val orderId: String,          // Runtime
    @Assisted private val userId: String,           // Runtime
    @Assisted("priority") private val isPriority: Boolean  // Runtime with qualifier
) {
    
    @AssistedFactory
    interface Factory {
        fun create(
            orderId: String,
            userId: String,
            @Assisted("priority") isPriority: Boolean
        ): OrderProcessor
    }
    
    suspend fun process(): Result<Order> {
        return try {
            val payment = paymentService.processPayment(orderId)
            val shipping = if (isPriority) {
                shippingService.expeditedShipping(orderId)
            } else {
                shippingService.standardShipping(orderId)
            }
            Result.success(Order(orderId, userId, payment, shipping))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

// Usage
class CheckoutViewModel @Inject constructor(
    private val orderProcessorFactory: OrderProcessor.Factory
) : ViewModel() {
    
    fun checkout(orderId: String, userId: String, isPriority: Boolean) {
        viewModelScope.launch {
            val processor = orderProcessorFactory.create(orderId, userId, isPriority)
            processor.process()
                .onSuccess { /* Handle success */ }
                .onFailure { /* Handle error */ }
        }
    }
}
```

## Assisted Injection with Interfaces

### Pattern: Factory for Interface

```kotlin
interface DataProcessor {
    suspend fun process(): Result<Unit>
}

class DataProcessorImpl @AssistedInject constructor(
    private val repository: DataRepository,
    @Assisted private val dataId: String
) : DataProcessor {
    
    @AssistedFactory
    interface Factory {
        fun create(dataId: String): DataProcessor
    }
    
    override suspend fun process(): Result<Unit> {
        return repository.processData(dataId)
    }
}

@Module
@InstallIn(ViewModelComponent::class)
interface DataProcessorModule {
    @Binds
    fun bindFactory(factory: DataProcessorImpl.Factory): DataProcessor.Factory
}
```

## Combining with Scoping

### Pattern: Scoped Factory

```kotlin
@ActivityRetainedScoped
class SessionManager @Inject constructor(
    private val api: SessionApi
) {
    private var currentSession: Session? = null
    
    fun getSession(): Session? = currentSession
    
    suspend fun createSession(userId: String): Session {
        return api.createSession(userId).also {
            currentSession = it
        }
    }
}

class SessionViewModel @AssistedInject constructor(
    private val sessionManager: SessionManager,  // Scoped dependency
    @Assisted private val userId: String
) : ViewModel() {
    
    @AssistedFactory
    interface Factory {
        fun create(userId: String): SessionViewModel
    }
    
    init {
        viewModelScope.launch {
            sessionManager.createSession(userId)
        }
    }
}
```

## Testing Assisted Injection

### Pattern: Test with Factory Mock

```kotlin
@HiltAndroidTest
class UserDetailViewModelTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @BindValue
    @JvmField
    val repository: UserRepository = mockk<UserRepository>()
    
    @Inject
    lateinit var viewModelFactory: UserDetailViewModel.Factory
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun `loads user on init`() = runTest {
        val user = User(id = "123", name = "Test")
        coEvery { repository.getUser("123") } returns user
        
        val viewModel = viewModelFactory.create("123")
        
        assertThat(viewModel.user.value).isEqualTo(user)
    }
}
```

### Pattern: Test with Manual Factory

```kotlin
@Test
fun `test order processor`() = runTest {
    val paymentService = mockk<PaymentService>()
    val shippingService = mockk<ShippingService>()
    
    // Manual factory for testing
    val factory = object : OrderProcessor.Factory {
        override fun create(
            orderId: String,
            userId: String,
            isPriority: Boolean
        ): OrderProcessor {
            return OrderProcessor(
                paymentService,
                shippingService,
                orderId,
                userId,
                isPriority
            )
        }
    }
    
    val processor = factory.create("order-1", "user-1", true)
    
    coEvery { paymentService.processPayment(any()) } returns Payment(...)
    coEvery { shippingService.expeditedShipping(any()) } returns Shipping(...)
    
    val result = processor.process()
    
    assertThat(result.isSuccess).isTrue()
}
```

## Common Patterns

### Pattern 1: ViewModel with Navigation Args
```kotlin
@HiltViewModel
class DetailViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    repository: Repository
) : ViewModel() {
    private val id: String = savedStateHandle["id"]!!
}
```

### Pattern 2: Worker with DI Dependencies
```kotlin
@HiltWorker
class MyWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    repository: Repository
) : CoroutineWorker(context, params)
```

### Pattern 3: Custom Factory for Complex Cases
```kotlin
class MyClass @AssistedInject constructor(
    dependency: Dependency,
    @Assisted param1: String,
    @Assisted param2: Int
) {
    @AssistedFactory
    interface Factory {
        fun create(param1: String, param2: Int): MyClass
    }
}
```

## Assisted Injection Checklist

- [ ] Use @AssistedInject on constructor
- [ ] Mark runtime parameters with @Assisted
- [ ] Define @AssistedFactory interface
- [ ] Inject factory, not the class directly
- [ ] Use @Assisted("name") for same-type parameters
- [ ] Combine with SavedStateHandle for ViewModels
- [ ] Use @HiltWorker for WorkManager integration
- [ ] Test by injecting factory and creating instances
- [ ] Consider scoping for factory dependencies
- [ ] Document which parameters are runtime vs DI
