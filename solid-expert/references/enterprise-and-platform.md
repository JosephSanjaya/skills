# Enterprise & Platform Architectures in Kotlin

Enterprise frameworks (like Spring Boot and Hibernate/JPA) and platform frameworks (like Android) have specific runtime environments that interact with Kotlin's default class design rules (such as classes being final by default).

---

## Spring Boot & CGLIB Proxying

By default, all Kotlin classes and methods are `final`. However, Spring Boot relies on subclassing classes at runtime via CGLIB proxies to implement cross-cutting concerns like `@Transactional`, `@Cacheable`, and `@Component` injection.

### Gradle Configuration
Apply the `kotlin-spring` or `kotlin-allopen` compiler plugins to automatically open Spring-managed classes:

```kotlin
// build.gradle.kts
plugins {
    kotlin("plugin.spring") version "2.1.0" // Auto-opens classes with Spring annotations
}
```

For custom annotations that require proxying, configure the `allopen` plugin:
```kotlin
plugins {
    kotlin("plugin.allopen") version "2.1.0"
}

allOpen {
    annotation("com.example.MyCustomProxyTarget")
}
```

*Note:* In Kotlin 2.2.0+, configure `-Xannotation-default-target=param-property` to align Kotlin properties with Spring's constructor dependency injection:
```kotlin
tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
    compilerOptions {
        freeCompilerArgs.add("-Xannotation-default-target=param-property")
    }
}
```

---

## JPA / Hibernate Entity Design

### Kotlin 2.3.0+ Automatic JPA Presets
In Kotlin 2.3.0+, applying the JPA plugin automatically applies both the `no-arg` compiler plugin and `all-open` preconfigured with the built-in JPA preset:

```kotlin
// build.gradle.kts
plugins {
    kotlin("plugin.jpa") version "2.3.0" // Automatically applies no-arg and all-open presets for JPA
}
```
This ensures that JPA entities are treated as open classes, allowing Hibernate to generate lazy-loading proxies automatically without manual configuration.

### Pre-Kotlin 2.3.0 Setup
In older Kotlin versions, you must apply and configure both plugins manually to prevent lazy loading failures:
```kotlin
plugins {
    kotlin("plugin.jpa") version "1.9.24" // Applies only no-arg
    kotlin("plugin.allopen") version "1.9.24"
}

allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}
```

---

## The `data class` Anti-Pattern for JPA Entities

Using a Kotlin `data class` for a JPA/Hibernate entity is a critical anti-pattern.

| Issue | Why | Impact |
|-------|-----|--------|
| **Proxy Failure** | `data class` is compiled as `final` and cannot be subclassed by CGLIB or Hibernate proxies. | Lazy loading fails, throwing `LazyInitializationException` or fetching everything eagerly. |
| **Circular StackOverflow** | Auto-generated `toString()`, `equals()`, and `hashCode()` evaluate all properties, traversing bidirectional relationships. | Triggers infinite recursion leading to `StackOverflowError` during serialization or logging. |
| **Eager Loading** | Accessing lazy-loaded collection fields during generated `toString` or `hashCode` evaluations initializes them. | Eviscerates database performance by triggering massive N+1 queries. |

### Best Practice: Idiomatic `open class` Entities
Configure entities as `open class`es, and manually implement `equals()` and `hashCode()` based on the database identifier (`id`) to ensure identity consistency across transient, managed, and detached states.

```kotlin
import jakarta.persistence.*
import org.hibernate.Hibernate

@Entity
@Table(name = "users")
open class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    open var id: Long? = null

    @Column(nullable = false, unique = true)
    open var username: String = ""

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other == null || Hibernate.getClass(this) != Hibernate.getClass(other)) return false
        other as User
        return id != null && id == other.id
    }

    override fun hashCode(): Int = id?.hashCode() ?: 0

    override fun toString(): String = "${this::class.simpleName}(id=$id, username='$username')"
}
```

---

## Android Lifecycle & UI Architectures

### ViewModel Delegation
Avoid bloated base view models (e.g. `BaseViewModel`) by extracting concerns (like billing, navigation, or tracking) into delegates and composing them inside ViewModels:

```kotlin
interface SubscriptionDelegate {
    val isPremium: StateFlow<Boolean>
    fun startMonitoring(scope: CoroutineScope)
}

class PremiumViewModel(
    subscriptionDelegate: SubscriptionDelegate
) : ViewModel(), SubscriptionDelegate by subscriptionDelegate {
    init {
        startMonitoring(viewModelScope) // Composition instead of base class inheritance
    }
}
```

### Fragment View Lifecycle Leaks
Fragment views are created and destroyed multiple times within a Fragment's overall lifecycle. Storing references (like View Binding) directly in class properties causes memory leaks unless they are set to null in `onDestroyView()`. Use a custom read-write property delegate to automate this:

```kotlin
import androidx.fragment.app.Fragment
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import kotlin.properties.ReadWriteProperty
import kotlin.reflect.KProperty

class AutoClearedDelegate<T : Any> : ReadWriteProperty<Fragment, T> {
    private var value: T? = null

    override fun getValue(thisRef: Fragment, property: KProperty<*>): T =
        value ?: error("Accessed before set or after view destroyed")

    override fun setValue(thisRef: Fragment, property: KProperty<*>, value: T) {
        thisRef.viewLifecycleOwner.lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onDestroy(owner: LifecycleOwner) {
                this@AutoClearedDelegate.value = null
            }
        })
        this.value = value
    }
}

// Fragment usage:
class MainFragment : Fragment() {
    private var binding: FragmentMainBinding by AutoClearedDelegate()
}
```

---

## Legitimate Uses of Inheritance: Sealed Taxonomies

Inheritance is valid and recommended when representing closed, finite sets of states (ADT - Algebraic Data Types), where compiler-enforced exhaustiveness is desired.

```kotlin
sealed interface UiState {
    data class Success(val data: List<String>) : UiState
    data class Error(val message: String) : UiState
    data object Loading : UiState
}

fun render(state: UiState) = when (state) {
    is UiState.Success -> showItems(state.data)
    is UiState.Error -> showError(state.message)
    UiState.Loading -> showSpinner()
    // No 'else' branch is required.
}
```
Adding new subtypes to `UiState` forces compiler errors at all `when` expressions, ensuring exhaustive state handling.
