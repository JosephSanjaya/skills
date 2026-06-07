# SOLID Principles through Composition

SOLID principles guide developers to build software that is easy to maintain, extend, and test. When combined with a **Composition over Inheritance** preference, these principles result in highly modular, decoupled architectures.

---

## 1. Single Responsibility Principle (SRP)

> "A class should have one, and only one, reason to change."

### Implementation via Composition
Instead of creating inheritance hierarchies or bloated subclasses that inherit multiple capabilities (e.g., logging, persistence, and tracking), SRP is best achieved by dividing distinct responsibilities into separate classes and composing them.

```kotlin
// ❌ BAD: God ViewModel doing UI state management, API requests, database queries, and analytics.
class OrderViewModel(
    private val api: OrderApi,
    private val database: OrderDatabase,
    private val analytics: Analytics
) : ViewModel() {
    fun loadOrders() {
        viewModelScope.launch {
            val response = api.getOrders()
            database.orderDao().insertAll(response)
            analytics.track("orders_loaded", response.size)
            _orders.value = response
        }
    }
}

// ✅ GOOD: Composing focused domain components. Each has a single responsibility.
class OrderViewModel(
    private val getOrdersUseCase: GetOrdersUseCase,
    private val analytics: Analytics
) : ViewModel() {
    private val _state = MutableStateFlow<OrderState>(OrderState.Loading)
    val state: StateFlow<OrderState> = _state.asStateFlow()
    
    fun loadOrders() {
        viewModelScope.launch {
            getOrdersUseCase()
                .onSuccess { orders ->
                    _state.value = OrderState.Success(orders)
                    analytics.track("orders_loaded", orders.size)
                }
                .onFailure { error ->
                    _state.value = OrderState.Error(error.message)
                }
        }
    }
}
```

---

## 2. Open/Closed Principle (OCP)

> "Software entities should be open for extension but closed for modification."

### Implementation via Composition
Avoid extending concrete classes to add behavior. Instead, define behaviors using interfaces or sealed class state taxonomies, and extend systems by supplying new implementations of these interfaces (polymorphism).

```kotlin
// ❌ BAD: Modifying a class or adding if/when statements every time a new payment type is introduced.
class PaymentViewModel : ViewModel() {
    fun processPayment(type: String, amount: Money) {
        when (type) {
            "credit_card" -> processCreditCard(amount)
            "paypal" -> processPayPal(amount)
        }
    }
}

// ✅ GOOD: Polymorphic extension. The view model is closed to modification but open to new payment methods.
interface PaymentProcessor {
    suspend fun process(method: PaymentMethod, amount: Money): Result<PaymentResult>
}

class PaymentViewModel(
    private val processor: PaymentProcessor
) : ViewModel() {
    fun processPayment(method: PaymentMethod, amount: Money) {
        viewModelScope.launch {
            processor.process(method, amount)
                .onSuccess { handleSuccess(it) }
                .onFailure { handleError(it) }
        }
    }
}
```

---

## 3. Liskov Substitution Principle (LSP)

> "Subtypes must be substitutable for their base types without altering program correctness."

### Implementation via Composition
Inheritance often violates LSP because base class authors cannot anticipate all subclass side-effects, leading to overridden methods throwing `NotImplementedError` or bypassing base constraints. Composition eliminates this risk by preventing subclasses from overriding internal concrete logic.

```kotlin
// ❌ BAD: Subtype violates the contract by throwing errors, making substitution unsafe.
interface OrderRepository {
    suspend fun getOrders(): List<Order>
}
class BrokenOrderRepository : OrderRepository {
    override suspend fun getOrders(): List<Order> {
        throw NotImplementedError() // Breaks program correctness
    }
}

// ✅ GOOD: Interoperable implementations conforming strictly to the monadic Result contract.
interface OrderRepository {
    suspend fun getOrders(): Result<List<Order>>
}
class RemoteOrderRepository(private val api: OrderApi) : OrderRepository {
    override suspend fun getOrders(): Result<List<Order>> = runCatching { api.getOrders() }
}
class CachedOrderRepository(private val dao: OrderDao) : OrderRepository {
    override suspend fun getOrders(): Result<List<Order>> = runCatching { dao.getOrders().map { it.toDomain() } }
}
```

---

## 4. Interface Segregation Principle (ISP)

> "Clients should not be forced to depend on methods they do not use."

### Implementation via Composition
Break fat, monolithic interfaces into small, cohesive ones. Classes can then implement multiple granular interfaces. Consumers can depend on only the interface segment they require, enabling lightweight composition.

```kotlin
// ❌ BAD: Fat interface forcing clients to depend on or implement unused methods.
interface UserRepository {
    suspend fun getUser(id: UserId): User
    suspend fun updateUser(user: User)
    suspend fun deleteUser(id: UserId)
    suspend fun getUserOrders(id: UserId): List<Order>
}

// ✅ GOOD: Split into segregated interfaces that can be composed.
interface UserReader {
    suspend fun getUser(id: UserId): User
}
interface UserWriter {
    suspend fun updateUser(user: User)
    suspend fun deleteUser(id: UserId)
}
interface UserOrdersReader {
    suspend fun getUserOrders(id: UserId): List<Order>
}

// ProfileViewModel only needs user profile data, not order histories
class ProfileViewModel(
    private val reader: UserReader,
    private val writer: UserWriter
) : ViewModel()
```

---

## 5. Dependency Inversion Principle (DIP)

> "High-level modules should not depend on low-level modules. Both should depend on abstractions."

### Implementation via Composition
High-level classes (like ViewModels or UseCases) must never instantiate low-level components (like Retrofit APIs or Room databases) directly. Instantiating concrete dependencies creates tight coupling. Instead, inject abstract dependencies (interfaces) via a DI container, composing the system dynamically.

```kotlin
// ❌ BAD: High-level class tightly coupled to low-level implementation details.
class OrderViewModel : ViewModel() {
    private val api = RetrofitOrderApi() // Direct dependency
    private val database = RoomOrderDatabase() // Direct dependency
}

// ✅ GOOD: Depending on abstractions. Low-level details are injected.
interface OrderRepository {
    suspend fun getOrders(): Result<List<Order>>
}
class OrderViewModel(
    private val repository: OrderRepository // Abstraction
) : ViewModel()
```

---

## Clean Architecture Dependency Rule
```
   [ UI Layer (Composables / ViewModels) ]
                     ↓
   [ Domain Layer (UseCases / Entities / Repository Interfaces) ]
                     ↑
   [ Data Layer (Repository Implementations / API / DB / Cache) ]
```
- **Dependencies point inward** towards the pure Domain layer.
- **Domain layer** is pure Kotlin, completely isolated from platform-specific frameworks (Android, iOS).
- **Data layer** implements repository interfaces defined by the Domain layer, decoupling business logic from platform code.
