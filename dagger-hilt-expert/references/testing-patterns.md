# Hilt Testing Patterns and Best Practices

## Testing Strategy Overview

```
Production Code          Test Replacement Strategy
─────────────────       ─────────────────────────
@InstallIn              @TestInstallIn (global, reusable)
SingletonComponent  →   @UninstallModules (per-test, expensive)
                        @BindValue (field injection, per-test)
```

## @TestInstallIn: Global Test Replacements

### Use Case: Replace Real Network with Fake

**Production Module:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideUserApi(retrofit: Retrofit): UserApi =
        retrofit.create(UserApi::class.java)
}
```

**Test Module (in test/ or androidTest/):**
```kotlin
@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [NetworkModule::class]
)
object FakeNetworkModule {
    @Provides
    @Singleton
    fun provideUserApi(): UserApi = FakeUserApi()
}
```

**Test:**
```kotlin
@HiltAndroidTest
class UserRepositoryTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @Inject
    lateinit var repository: UserRepository
    
    @Inject
    lateinit var fakeApi: UserApi  // Gets FakeUserApi
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun `test user fetch`() = runTest {
        (fakeApi as FakeUserApi).setResponse(User(id = "1", name = "Test"))
        val user = repository.getUser("1")
        assertThat(user.name).isEqualTo("Test")
    }
}
```

**Benefits:**
- ✅ Component reused across all tests (fast builds)
- ✅ No need to repeat replacement in every test
- ✅ Consistent fake behavior across test suite

## @UninstallModules: Per-Test Replacements

### Use Case: Test-Specific Mock Behavior

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AnalyticsModule {
    @Provides
    @Singleton
    fun provideAnalytics(): Analytics = FirebaseAnalytics()
}

@HiltAndroidTest
@UninstallModules(AnalyticsModule::class)  // ⚠️ Generates unique component
class LoginViewModelTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @Module
    @InstallIn(SingletonComponent::class)
    object TestAnalyticsModule {
        @Provides
        @Singleton
        fun provideAnalytics(): Analytics = mockk<Analytics>(relaxed = true)
    }
    
    @Inject
    lateinit var analytics: Analytics
    
    @Test
    fun `test login tracks event`() {
        // Test with mock
    }
}
```

**Drawbacks:**
- ⚠️ Unique component generated per test class (slow builds)
- ⚠️ Use sparingly, prefer @TestInstallIn

## @BindValue: Field Injection for Tests

### Use Case: Quick Mock Injection

```kotlin
@HiltAndroidTest
class PaymentViewModelTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @BindValue
    @JvmField
    val paymentProcessor: PaymentProcessor = mockk<PaymentProcessor>()
    
    @Inject
    lateinit var viewModel: PaymentViewModel
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun `test payment success`() = runTest {
        coEvery { paymentProcessor.process(any()) } returns Result.success(Unit)
        
        viewModel.processPayment(PaymentInfo(...))
        
        assertThat(viewModel.state.value).isInstanceOf(PaymentState.Success::class.java)
    }
}
```

### Critical: Initialize at Declaration with ActivityScenarioRule

```kotlin
@HiltAndroidTest
class LoginActivityTest {
    @get:Rule(order = 0)
    var hiltRule = HiltAndroidRule(this)
    
    @get:Rule(order = 1)
    var activityRule = ActivityScenarioRule(LoginActivity::class.java)
    
    // ✅ Good: Initialized at declaration
    @BindValue
    @JvmField
    val authService: AuthService = mockk<AuthService>(relaxed = true)
    
    // ❌ Bad: Would be null when Activity is created
    // @BindValue
    // @JvmField
    // lateinit var authService: AuthService
    
    @Test
    fun `test login button click`() {
        coEvery { authService.login(any(), any()) } returns Result.success(User(...))
        
        onView(withId(R.id.loginButton)).perform(click())
        
        onView(withId(R.id.welcomeText)).check(matches(isDisplayed()))
    }
}
```

**Why:** ActivityScenarioRule creates the Activity before @Before methods run, so @BindValue fields must be initialized at declaration time.

## Testing ViewModels with Hilt

### Pattern: ViewModel Test with Repository Mock

```kotlin
@HiltViewModel
class UserViewModel @Inject constructor(
    private val repository: UserRepository
) : ViewModel() {
    private val _state = MutableStateFlow<UiState>(UiState.Loading)
    val state: StateFlow<UiState> = _state.asStateFlow()
    
    fun loadUser(id: String) {
        viewModelScope.launch {
            _state.value = UiState.Loading
            repository.getUser(id)
                .onSuccess { _state.value = UiState.Success(it) }
                .onFailure { _state.value = UiState.Error(it.message) }
        }
    }
}

@HiltAndroidTest
class UserViewModelTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @BindValue
    @JvmField
    val repository: UserRepository = mockk<UserRepository>()
    
    private lateinit var viewModel: UserViewModel
    
    @Before
    fun setup() {
        hiltRule.inject()
        viewModel = UserViewModel(repository)
    }
    
    @Test
    fun `loadUser success updates state`() = runTest {
        val user = User(id = "1", name = "Test")
        coEvery { repository.getUser("1") } returns Result.success(user)
        
        viewModel.loadUser("1")
        
        assertThat(viewModel.state.value).isEqualTo(UiState.Success(user))
    }
    
    @Test
    fun `loadUser failure updates state`() = runTest {
        coEvery { repository.getUser("1") } returns Result.failure(Exception("Network error"))
        
        viewModel.loadUser("1")
        
        assertThat(viewModel.state.value).isInstanceOf(UiState.Error::class.java)
    }
}
```

## Testing Fragments with Hilt

### Pattern: Fragment Test with launchFragmentInHiltContainer

```kotlin
@AndroidEntryPoint
class UserProfileFragment : Fragment() {
    @Inject lateinit var repository: UserRepository
    private val viewModel: UserViewModel by viewModels()
}

@HiltAndroidTest
class UserProfileFragmentTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @BindValue
    @JvmField
    val repository: UserRepository = FakeUserRepository()
    
    @Test
    fun `displays user name`() {
        launchFragmentInHiltContainer<UserProfileFragment> {
            // Fragment is now created with injected dependencies
        }
        
        onView(withId(R.id.userName)).check(matches(withText("Test User")))
    }
}
```

## Fake vs Mock Strategy

### Fake: Lightweight In-Memory Implementation

```kotlin
class FakeUserRepository : UserRepository {
    private val users = mutableMapOf<String, User>()
    
    override suspend fun getUser(id: String): Result<User> {
        return users[id]?.let { Result.success(it) }
            ?: Result.failure(Exception("User not found"))
    }
    
    override suspend fun saveUser(user: User): Result<Unit> {
        users[user.id] = user
        return Result.success(Unit)
    }
    
    // Test helpers
    fun addUser(user: User) {
        users[user.id] = user
    }
    
    fun clear() {
        users.clear()
    }
}
```

**Use Fakes When:**
- Testing integration between multiple components
- Need realistic behavior (e.g., database queries)
- Want to avoid brittle verification logic

### Mock: Behavior Verification

```kotlin
@Test
fun `saveUser calls repository`() = runTest {
    val repository = mockk<UserRepository>()
    val viewModel = UserViewModel(repository)
    val user = User(id = "1", name = "Test")
    
    coEvery { repository.saveUser(user) } returns Result.success(Unit)
    
    viewModel.saveUser(user)
    
    coVerify { repository.saveUser(user) }
}
```

**Use Mocks When:**
- Testing specific interactions
- Verifying method calls and arguments
- Simulating error conditions

## Testing with Custom Test Runner

### Setup: Custom Application for Tests

```kotlin
// src/androidTest/kotlin/CustomTestRunner.kt
class CustomTestRunner : AndroidJUnitRunner() {
    override fun newApplication(
        cl: ClassLoader?,
        className: String?,
        context: Context?
    ): Application {
        return super.newApplication(cl, HiltTestApplication::class.java.name, context)
    }
}

// build.gradle.kts
android {
    defaultConfig {
        testInstrumentationRunner = "com.example.CustomTestRunner"
    }
}
```

## Testing Scoped Dependencies

### Pattern: Testing ActivityRetainedScoped

```kotlin
@Module
@InstallIn(ActivityRetainedComponent::class)
object CheckoutModule {
    @Provides
    @ActivityRetainedScoped
    fun provideCheckoutSession(): CheckoutSession = CheckoutSessionImpl()
}

@HiltAndroidTest
class CheckoutFlowTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @get:Rule
    var activityRule = ActivityScenarioRule(CheckoutActivity::class.java)
    
    @Test
    fun `checkout session persists across rotation`() {
        // Add item to cart
        onView(withId(R.id.addToCartButton)).perform(click())
        
        // Rotate device
        activityRule.scenario.recreate()
        
        // Verify item still in cart (same CheckoutSession instance)
        onView(withId(R.id.cartItemCount)).check(matches(withText("1")))
    }
}
```

## Testing with Coroutines

### Pattern: Testing Suspend Functions

```kotlin
@HiltAndroidTest
class UserRepositoryTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @BindValue
    @JvmField
    val api: UserApi = FakeUserApi()
    
    @Inject
    lateinit var repository: UserRepository
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun `getUser returns cached user`() = runTest {
        val user = User(id = "1", name = "Test")
        (api as FakeUserApi).addUser(user)
        
        // First call fetches from API
        val result1 = repository.getUser("1")
        assertThat(result1.getOrNull()).isEqualTo(user)
        
        // Second call returns cached
        (api as FakeUserApi).clear()
        val result2 = repository.getUser("1")
        assertThat(result2.getOrNull()).isEqualTo(user)
    }
}
```

## Build Performance Optimization

### Strategy: Minimize @UninstallModules Usage

```kotlin
// ❌ Bad: Every test class uses @UninstallModules
@HiltAndroidTest
@UninstallModules(NetworkModule::class)
class Test1 { ... }

@HiltAndroidTest
@UninstallModules(NetworkModule::class)
class Test2 { ... }

// ✅ Good: Single @TestInstallIn replacement
@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [NetworkModule::class]
)
object FakeNetworkModule { ... }

@HiltAndroidTest
class Test1 { ... }  // Reuses same component

@HiltAndroidTest
class Test2 { ... }  // Reuses same component
```

**Impact:** Can reduce test build time by 50%+ in large projects.

## Testing Checklist

- [ ] Use @TestInstallIn for global fakes (network, database)
- [ ] Reserve @UninstallModules for truly test-specific behavior
- [ ] Initialize @BindValue fields at declaration when using ActivityScenarioRule
- [ ] Prefer fakes over mocks for integration tests
- [ ] Use runTest for coroutine testing
- [ ] Test scoped dependencies across lifecycle events
- [ ] Verify cleanup in onCleared() for ViewModels
- [ ] Use custom test runner for Hilt tests
