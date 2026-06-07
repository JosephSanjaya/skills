# COI Patterns and Recipes

## Class Delegation Bytecode

Kotlin `by` keyword generates:
- Private synthetic field `$$delegate_0` (final)
- Public forwarding methods per interface member (direct INVOKEINTERFACE, no reflection)

```kotlin
class Window(sizable: Sizable) : Sizable by sizable
// Decompiles to:
// private final Sizable $$delegate_0;
// public int getWidth() { return $$delegate_0.getWidth(); }
```

Zero reflection overhead. Direct static dispatch.

## Encapsulated Constructor

Prevent delegate injection via private primary + public secondary:
```kotlin
class SecureSocket private constructor(
    private val channel: NetworkChannel
) : NetworkChannel by channel {
    constructor() : this(DefaultNetworkChannel(timeout = 5000))
}
```

## Interface Segregation (ISP) + Multi-Delegation

Small, focused interfaces → compose multiple:
```kotlin
interface Renderable { fun render() }
interface Clickable { fun click() }

class Button(
    renderer: Renderable,
    clickHandler: Clickable
) : Renderable by renderer, Clickable by clickHandler
```

## Refactoring Recipe (Inheritance → Composition)

| Step | Action |
|------|--------|
| 1 | Identify orthogonal behavior dimensions |
| 2 | Remove `abstract` from base class |
| 3 | Extract abstract methods into focused interfaces |
| 4 | Convert subclasses to interface implementations |
| 5 | Inject via DI or factory |

```kotlin
// Before: deep hierarchy
abstract class AbstractGameStateSaver { abstract fun save(state: GameState) }
// + JsonGameStateSaver, FileGameStateSaver, JsonFileGameStateSaver...

// After: composed
interface StateEncoder { fun encode(state: GameState): ByteArray }
interface PersistenceEngine { fun persist(data: ByteArray) }

class GameStateSaver(
    private val encoder: StateEncoder,
    private val persistence: PersistenceEngine
) {
    fun save(state: GameState) = persistence.persist(encoder.encode(state))
}

// New format/storage = new impl, zero changes to GameStateSaver
```

## ViewModel Delegation (Android)

```kotlin
interface SubscriptionDelegate {
    val isPremium: StateFlow<Boolean>
    fun monitorBillingScope(scope: CoroutineScope)
}

class PremiumViewModel(
    subscriptionDelegate: SubscriptionDelegate
) : ViewModel(), SubscriptionDelegate by subscriptionDelegate {
    init { monitorBillingScope(viewModelScope) }
}
```
Avoids `BaseBillingViewModel` inheritance chain. Subscription logic testable in isolation.

## Value Classes (Zero-Cost Domain Wrappers)

```kotlin
@JvmInline
value class AccountId(val rawId: String)
@JvmInline
value class Currency(val amount: BigDecimal)
```
JVM erases wrapper at runtime → compile-time safety, zero allocation overhead.

## Lazy Thread-Safety Modes

```kotlin
// Default — synchronized, lock on every access
val heavyShared by lazy { ExpensiveSharedObject() }

// NONE — single-thread only, no lock overhead
val mainThreadWidget by lazy(LazyThreadSafetyMode.NONE) { ExpensiveUIWidget() }

// PUBLICATION — concurrent safe, no strong exclusion
val concurrent by lazy(LazyThreadSafetyMode.PUBLICATION) { SafeObject() }
```

Use `NONE` for UI-thread-only properties (avoids `SYNCHRONIZED` lock monitor contention).

## Memory Leak Prevention (Android)

Non-capturing lambda = JVM singleton, no enclosing reference:
```kotlin
val work = Runnable { println("safe") } // singleton

var index = 0
val leaking = Runnable { println(index) } // captures index → enclosing ref
```

Tie async delegates to lifecycle scope:
```kotlin
// Fragment
viewLifecycleOwner.lifecycleScope.launch { ... }
// ViewModel
viewModelScope.launch { ... }
```
