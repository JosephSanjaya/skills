# Composition Over Inheritance: Patterns & Pitfalls

Composition over inheritance (COI) builds flexible codebases by combining objects with small, focused responsibilities, rather than creating deep inheritance hierarchies that leak base class implementation details.

---

## Kotlin Class Delegation (`by`) Bytecode Analysis

Kotlin's `by` keyword enables native interface delegation, where the compiler generates boilerplate forwarding code.

```kotlin
interface Sizable { val width: Int }
class Window(sizable: Sizable) : Sizable by sizable
```

Under the hood, the compiler decompiles this to direct JVM instructions:
- Generates a `private final Sizable $$delegate_0` synthetic field.
- Generates a public wrapper method `public int getWidth() { return $$delegate_0.getWidth(); }`.
- Dispatches using direct `INVOKEINTERFACE` calls, meaning there is **zero reflection overhead** and it enjoys static-like dispatch performance.

---

## COI Patterns

### 1. Encapsulated Constructor
Hide delegation implementation details using a private primary constructor and a public secondary constructor:
```kotlin
class SecureSocket private constructor(
    private val channel: NetworkChannel
) : NetworkChannel by channel {
    // Secondary constructor hides default delegation instantiation from consumers
    constructor() : this(DefaultNetworkChannel(timeout = 5000))
}
```

### 2. Multi-Delegation + Interface Segregation
Compose a single class out of multiple focused behaviors:
```kotlin
interface Renderable { fun render() }
interface Clickable { fun click() }

class Button(
    renderer: Renderable,
    clickHandler: Clickable
) : Renderable by renderer, Clickable by clickHandler
```

### 3. Refactoring Recipe: Inheritance to Composition
1. **Identify Orthogonal Behaviors**: Break down abstract parent duties into independent dimensions (e.g. data encoding vs data saving).
2. **Remove Class Inheritance**: Make the parent class concrete or remove it.
3. **Extract Interfaces**: Turn abstract methods into separate interfaces.
4. **Inject Dependencies**: Inject implementations of these interfaces into the client class rather than inheriting them.

```kotlin
// Before: Abstract hierarchies that multiply subclass permutations
abstract class AbstractGameStateSaver { abstract fun save(state: GameState) }
// Subclasses: JsonGameStateSaver, FileGameStateSaver, JsonFileGameStateSaver, etc.

// After: Decoupled composition
interface StateEncoder { fun encode(state: GameState): ByteArray }
interface PersistenceEngine { fun persist(data: ByteArray) }

class GameStateSaver(
    private val encoder: StateEncoder,
    private val persistence: PersistenceEngine
) {
    fun save(state: GameState) = persistence.persist(encoder.encode(state))
}
```

### 4. Zero-Cost Value Classes
Wrap primitive types in type-safe domain wrappers.
```kotlin
@JvmInline value class UserId(val value: String)
@JvmInline value class Email(val value: String) {
    init { require(value.contains("@")) { "Invalid email address" } }
}

// ❌ Primitive Obsession: fun createUser(id: String, email: String)
// ✅ Type-safe: fun createUser(id: UserId, email: Email)
```
The JVM erases the wrapper class at runtime, using the raw underlying type, achieving **zero allocation overhead**.

### 5. Lazy Thread-Safety Modes
Optimize properties utilizing `by lazy` based on execution context:
- `LazyThreadSafetyMode.SYNCHRONIZED`: (Default) Thread-safe; uses a lock on every thread read.
- `LazyThreadSafetyMode.PUBLICATION`: Safe for concurrent initialization, but allows multiple threads to compute the initializer concurrently (only the first completed is stored).
- `LazyThreadSafetyMode.NONE`: **Not thread-safe**. Use for UI/Main Thread-bound variables (e.g. Android Compose/View elements) to avoid synchronization monitor overhead.

---

## Critical Delegation Pitfalls

### Pitfall 1: Loss of Self (this Escape)
The delegate has no reference to the wrapping class. Method invocations inside the delegate resolve to the delegate instance itself (`this`), bypassing any method overrides inside the wrapper class.

```kotlin
interface Printer {
    val message: String
    fun printMessage()
}
class SimplePrinter : Printer {
    override val message = "SimplePrinter"
    override fun printMessage() = println(message) // resolving on 'this'
}
class VerbosePrinter(delegate: Printer) : Printer by delegate {
    override val message = "VerbosePrinter"
}
// VerbosePrinter(SimplePrinter()).printMessage() -> Prints "SimplePrinter"!
```
**Fix:** Manually override coordinating methods inside the wrapper class:
```kotlin
class VerbosePrinter(private val delegate: Printer) : Printer by delegate {
    override val message = "VerbosePrinter"
    override fun printMessage() = println(message) // Explicit override prints "VerbosePrinter"
}
```

### Pitfall 2: Mutable Constructor Delegate Trap
Declaring a delegate parameter in a constructor as `var` makes the property mutable, but the backing synthetic `$$delegate_0` field is compiled as a `final` field. Reassigning the property does not update the delegate forwarding target.

```kotlin
class StrategyRunner(var strategy: ExecutionStrategy) : ExecutionStrategy by strategy
val runner = StrategyRunner(StrategyA())
runner.strategy = StrategyB()
runner.execute() // ❌ Executes StrategyA! Backing delegate field is immutable.
```
**Fix:** Write manual method forwarding instead of using `by` delegation:
```kotlin
class DynamicStrategyRunner(var strategy: ExecutionStrategy) : ExecutionStrategy {
    override fun execute() = strategy.execute() // Reassignment works correctly
}
```

### Pitfall 3: Java Default Method Bypass
Kotlin delegation does not generate wrappers for default interface methods declared in Java 8+ interfaces. If a class implements the Java interface and delegates it, the JVM calls the interface's default method directly, bypassing delegate overrides.

```java
// Java Interface
public interface MessageService {
    default void dispatch(String msg) { System.out.println("Default: " + msg); }
}
```
```kotlin
class SecureMessageService : MessageService {
    override fun dispatch(msg: String) = println("Encrypted: $msg")
}
class MessageDispatcher(service: MessageService) : MessageService by service
// MessageDispatcher(SecureMessageService()).dispatch("Hi") -> Prints "Default: Hi"!
```
**Fix:** Manually override the method in the Kotlin delegator:
```kotlin
class MessageDispatcher(private val service: MessageService) : MessageService by service {
    override fun dispatch(msg: String) = service.dispatch(msg)
}
```

### Pitfall 4: Any Methods Gap (equals/hashCode/toString)
Class delegation (`by`) does not forward standard JVM `equals()`, `hashCode()`, or `toString()` calls. It retains default reference equality checking on the wrapper object.
**Fix:** Explicitly override `equals`, `hashCode`, and `toString` on the delegating wrapper, forwarding checks to the backing delegate or checking fields manually.

### Pitfall 5: Interface-Only Constraint
Kotlin class delegation requires the target to be an interface. You cannot delegate to abstract or concrete classes. This constraint prevents compiler initialization bypasses and class layout hierarchy collisions.
