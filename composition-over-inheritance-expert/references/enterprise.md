# Enterprise & Platform Contexts

## Spring Boot + CGLIB

Kotlin `final` by default breaks Spring proxy generation (`@Transactional`, `@Cacheable`, `@Component`).

**Fix:** Add compiler plugins to `build.gradle.kts`:
```kotlin
plugins {
    kotlin("plugin.spring") version "2.3.20" // auto-opens Spring-annotated classes
}
```

### Manual Configuration (Pre-configured by plugin.spring)
If custom annotations require opening:
```kotlin
plugins {
    kotlin("plugin.allopen") version "2.3.20"
}
allOpen {
    annotation("com.example.MyCustomComponent")
}
```

*Note:* In Kotlin 2.2.0+, it is recommended to configure the `-Xannotation-default-target=param-property` compiler flag for compatibility with Spring's constructor dependency injection and new defaulting rules:
```kotlin
tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
    kotlinOptions {
        freeCompilerArgs += "-Xannotation-default-target=param-property"
    }
}
```

---

## JPA/Hibernate

### Kotlin 2.3.20+ (Recommended)
Starting with Kotlin 2.3.20, the `kotlin("plugin.jpa")` plugin automatically applies the `all-open` plugin with the built-in JPA preset, in addition to applying the `no-arg` compiler plugin.

This ensures that:
- JPA entities are automatically treated as `open`.
- Lazy associations (e.g. `@OneToMany`, `@ManyToOne`) work as expected out-of-the-box instead of causing eager loading.
- Synthetic zero-argument constructors are generated automatically.

```kotlin
plugins {
    kotlin("plugin.jpa") version "2.3.20" // Automatically applies no-arg and all-open JPA presets
}
```

### Pre-Kotlin 2.3.20
In older Kotlin versions, you must apply both plugins manually to make lazy-loading work:
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

Never use a `data class` for JPA/Hibernate entities.

| Problem | Why | Impact |
|---------|-----|--------|
| **Proxy Failure** | `data class` is compiled as `final` and cannot be subclassed by Hibernate/CGLIB proxies. | Lazy-loading fails, throwing `LazyInitializationException` or loading everything eagerly. |
| **Circular StackOverflow** | Auto-generated `equals()`, `hashCode()`, and `toString()` evaluate all properties, including bidirectional relationships. | Causes infinite recursion and `StackOverflowError` when print/inspecting or using collections. |
| **Eager Initialization** | Accessing properties inside the generated `toString`/`hashCode`/`equals` methods triggers initialization of lazy-loaded fields. | Violates lazy-loading, causing severe performance issues (N+1 queries). |

### Best Practice: standard `open class`
JPA entities should be standard `open class`es, with `equals()` and `hashCode()` manually overridden using the database identifier (`id`) to ensure object identity consistency across entity lifecycle states (Transient, Managed, Detached).

```kotlin
import jakarta.persistence.*
import org.hibernate.Hibernate

@Entity
@Table(name = "users")
open class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    open var id: Long? = null

    @Column(nullable = false)
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

## Android Lifecycle + Delegation

Property delegate memory cleanup on Fragment view destruction is necessary to avoid memory leaks:
```kotlin
import androidx.fragment.app.Fragment
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import kotlin.properties.ReadWriteProperty
import kotlin.reflect.KProperty

class AutoClearedDelegate<T : Any> : ReadWriteProperty<Fragment, T> {
    private var value: T? = null
    
    override fun getValue(thisRef: Fragment, property: KProperty<*>): T =
        value ?: error("Accessed after view destroyed or before set")
    
    override fun setValue(thisRef: Fragment, property: KProperty<*>, value: T) {
        thisRef.viewLifecycleOwner.lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onDestroy(owner: LifecycleOwner) {
                this@AutoClearedDelegate.value = null
            }
        })
        this.value = value
    }
}

// Usage inside Fragment
class MainFragment : Fragment() {
    private var binding: FragmentMainBinding by AutoClearedDelegate()
}
```

---

## Sealed Classes (Legitimate Inheritance)

Inheritance is highly appropriate for representing closed, finite sets of states where polymorphism is required.

```kotlin
sealed interface UiState {
    data class Success(val data: List<String>) : UiState
    data class Error(val message: String) : UiState
    data object Loading : UiState
}

// Compiler enforces exhaustiveness (no 'else' needed)
fun render(state: UiState) {
    when (state) {
        is UiState.Success -> showData(state.data)
        is UiState.Error -> showError(state.message)
        UiState.Loading -> showSpinner()
    }
}
```
Adding a new subtype to `UiState` will trigger compile-time errors at all `when` expressions, ensuring safety.
