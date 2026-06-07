# Delegation Pitfalls

## 1. Loss of Self (this Escape)

Delegate has NO knowledge of the delegating wrapper. Self-use calls inside delegate do NOT route to delegator overrides.

```kotlin
interface Printer {
    val message: String
    fun printMessage()
}
class SimplePrinter : Printer {
    override val message = "SimplePrinter"
    override fun printMessage() = println(message) // calls THIS.message
}
class VerbosePrinter(delegate: Printer) : Printer by delegate {
    override val message = "VerbosePrinter"
}
// VerbosePrinter().printMessage() → prints "SimplePrinter"!
```

**Fix:** Explicitly override coordinating methods in delegator:
```kotlin
class VerbosePrinter(private val delegate: Printer) : Printer by delegate {
    override val message = "VerbosePrinter"
    override fun printMessage() = println(message) // now routes correctly
}
```

## 2. Mutable Constructor Delegate Trap

`var` delegate in constructor → compiler creates TWO fields: mutable property + final `$$delegate_0`. Reassigning `var` does NOT update forwarding target.

```kotlin
class StrategyRunner(var strategy: ExecutionStrategy) : ExecutionStrategy by strategy
val runner = StrategyRunner(StrategyA())
runner.strategy = StrategyB()
runner.execute() // Still executes StrategyA!
```

**Fix:** Manual forwarding for dynamic delegates:
```kotlin
class DynamicStrategyRunner(var strategy: ExecutionStrategy) : ExecutionStrategy {
    override fun execute() = strategy.execute()
}
```

## 3. Java Default Method Bypass

Kotlin delegation generates NO forwarding for Java 8+ default methods. Delegate overrides silently bypassed.

```java
public interface MessageService {
    default void dispatch(String msg) { System.out.println("Default: " + msg); }
}
```
```kotlin
class SecureMessageService : MessageService {
    override fun dispatch(msg: String) = println("Encrypted: $msg")
}
class MessageDispatcher(service: MessageService) : MessageService by service
// MessageDispatcher(SecureMessageService()).dispatch("Hi") → "Default: Hi"!
```

**Fix:** Manually override in delegator:
```kotlin
class MessageDispatcher(private val service: MessageService) : MessageService by service {
    override fun dispatch(msg: String) = service.dispatch(msg)
}
```

IntelliJ inspection: `JavaDefaultMethodsNotOverriddenByDelegation`

## 4. Any Methods Gap (equals/hashCode/toString)

`equals()`, `hashCode()`, `toString()` NOT forwarded — uses JVM Object defaults (reference equality).

**Fix option A:** Declare in interface:
```kotlin
interface ComparableCollection : Collection<String> {
    override fun equals(other: Any?): Boolean
    override fun hashCode(): Int
}
```

**Fix option B:** Manually implement in delegating class.

## 5. Interface-Only Constraint

`by` clause target MUST be an interface. Cannot delegate to abstract/concrete classes.

Reasons:
- Concrete methods are `final` by default — can't override
- Constructor chaining bypassed → incomplete init
- `Any` method ambiguity (equals/hashCode/toString)
