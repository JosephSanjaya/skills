# Clean Code, Object Stereotypes & Testing in Kotlin

Professional mobile craftsmanship is achieved through strict coding standards, clear object design stereotypes, exhaustive test coverage, and a disciplined test-driven development (TDD) cycle.

---

## Clean Kotlin Structure Rules

- **Limit Sizes**: Keep functions under 10 lines and classes under 50 lines. Large sizes indicate mixed responsibilities.
- **Prefer Expressions**: Use expression bodies (`fun getAge() = 25`) and `when` expressions to reduce nesting and syntax noise.
- **Enforce Immutable State**: Prefer `val` over `var` and `List` over `MutableList`. Use `copy()` on data classes for mutations.
- **Use Early Returns**: Apply guard clauses to handle invalid inputs immediately, preventing deep nesting:
  ```kotlin
  fun processEmail(email: Email) {
      if (!email.value.contains("@")) return
      // core logic...
  }
  ```
- **Ban Red Flags**: Never use `!!` (unsafe cast) or `runBlocking` (blocks threads, causing ANRs in mobile) in production code.

---

## Object Design Stereotypes

To maintain a clean SOLID architecture, categorize every class into one of the following stereotypes:

| Stereotype | Purpose | Mutable? | Android Imports? |
|------------|---------|----------|-------------------|
| **Service** | Orchestrates tasks or encapsulates business logic (e.g. UseCases, Repositories). | No (Stateless) | No |
| **Entity** | Represents domain objects with a unique identifier. | Yes (Entity fields) | No |
| **Value Object** | Wraps raw values (e.g. `UserId`, `Email`) with self-contained validation. | No | No |
| **Controller / Presenter** | Handles input and binds data to views (e.g. ViewModels). | Yes (UI State Flow) | Yes |
| **Factory** | Encapsulates the instantiation of complex composed objects. | No | No |

---

## Code Smells & Refactoring Solutions

| Code Smell | Description | Refactoring Action |
|------------|-------------|--------------------|
| **Primitive Obsession** | Using raw primitive types (`String`, `Int`) to represent domain items. | Wrap inside `@JvmInline value class` wrappers. |
| **Long Parameter List** | Functions passing 4+ parameters. | Extract parameters into a data class / parameter object. |
| **Switch Statements** | Heavy `when` chains performing action based on type. | Use polymorphism / sealed classes. |
| **Speculative Generality** | Designing complex generic layers "just in case" they are needed (YAGNI). | Code for the concrete requirement; refactor only when needed. |
| **Feature Envy** | A class that accesses another object's fields more than its own. | Move the method to the class containing the data. |

---

## Testing Stack & Best Practices

Verify all domain logic in isolation utilizing JUnit, MockK, and Turbine.

- **JUnit 5**: Standard unit testing framework.
- **MockK**: Idiomatic mocking library for Kotlin.
- **Turbine**: Flow testing library.
- **Robolectric**: Fast, headless local Android unit testing.

### Testing StateFlows with Turbine
Turbine enables assertion of Flow emissions sequentially. Use `runTest` to execute coroutine blocks on a test dispatcher:

```kotlin
import app.cash.turbine.test
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class OrderViewModelTest {
    private val getOrdersUseCase: GetOrdersUseCase = mockk()
    private val viewModel = OrderViewModel(getOrdersUseCase, mockk(relaxed = true))

    @Test
    fun `emits Loading then Success states`() = runTest {
        val orders = listOf(Order(id = OrderId("123")))
        coEvery { getOrdersUseCase() } returns Result.success(orders)

        viewModel.state.test {
            // Assert first emission
            assertEquals(OrderState.Loading, awaitItem())
            
            // Trigger action
            viewModel.loadOrders()
            
            // Assert subsequent emission
            assertEquals(OrderState.Success(orders), awaitItem())
        }
    }
}
```

---

## Test-Driven Development (TDD) Workflow

TDD minimizes bugs and improves code structures through short, iterative cycles:

1. **Red**: Write a failing unit test that describes the desired behavior. Ensure it fails compilation or execution.
2. **Green**: Write the simplest code possible to make the test pass. Do not write extra code or worry about clean design yet.
3. **Refactor**: Clean up the code (remove duplication, apply SOLID principles, extract classes) while ensuring the test suite remains green.
