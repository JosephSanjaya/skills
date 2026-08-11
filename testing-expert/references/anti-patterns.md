# Test Anti-Patterns (Kotlin)

Each anti-pattern below reduces a test's value by damaging one or more of the four pillars.

---

<anti-patterns>

<pattern id="AP1">

## 1. Testing private methods directly

**Pillar damaged:** Resistance to refactoring  
**Why it happens:** Private method is complex and feels like it needs coverage.

Exposing private methods for tests couples tests to implementation — the definition of fragility. If the private logic is too complex to test through the public API, extract the abstraction into its own class.

```kotlin
// ❌ Making internal just for test access
class PriceCalculator {
    internal fun applyTax(price: Double): Double = price * 1.21  // exposed for test
}

// ✅ Extract into its own testable class
class TaxCalculator {
    fun apply(price: Double): Double = price * 1.21
}
// Now test TaxCalculator directly via its public API
```

</pattern>

---

<pattern id="AP2">

## 2. Exposing private state for assertions

**Pillar damaged:** Resistance to refactoring  
**Why it happens:** Can't see the state change from outside the class.

Tests must interact with the SUT as production code does — no special privileges. If state isn't observable by production code, it's an implementation detail; test the observable outcome instead.

```kotlin
// ❌ Status exposed only for tests
class Customer(val status: CustomerStatus = CustomerStatus.Regular) {  // public for test
    fun promote() { /* changes status */ }
}
// Test wrongly asserts: customer.status shouldBe CustomerStatus.Preferred

// ✅ Test the observable outcome production code actually uses
customer.promote()
customer.discountRate() shouldBe 0.05  // this is what callers care about
```

</pattern>

---

<pattern id="AP3">

## 3. Leaking domain knowledge into tests

**Pillar damaged:** Protection against regressions, resistance to refactoring  
**Why it happens:** Parameterized test tries to be "smart" with expected values.

When the test re-implements the algorithm to compute expected values, both sides carry the same bug and the test can never catch a wrong implementation. Hard-code expected values instead, computed independently.

```kotlin
// ❌ Duplicates the algorithm — if logic is wrong, both sides are wrong
test("discount is applied") {
    val price = 100.0
    val expected = price * 0.9  // leaks the algorithm!
    sut.applyDiscount(price) shouldBe expected
}

// ✅ Hard-coded values computed independently
withData(
    100.0 to 90.0,
    50.0 to 45.0,
    200.0 to 180.0,
) { (input, expected) ->
    sut.applyDiscount(input) shouldBe expected
}
```

</pattern>

---

<pattern id="AP4">

## 4. Code pollution

**Pillar damaged:** Maintainability  
**Why it happens:** Test needs to disable a side effect (logging, file writes) during runs.

Adding test-only switches (`isTestEnvironment`, `isMock`) to production code mixes concerns and creates hidden code paths that exist only for tests. Use an interface with separate implementations.

```kotlin
// ❌ isTestEnvironment pollutes production class
class AuditLogger(private val isTestEnvironment: Boolean) {
    fun log(event: String) { if (!isTestEnvironment) writeToFile(event) }
}

// ✅ Interface — production code is clean, tests get a no-op
interface AuditLogger { fun log(event: String) }
class FileAuditLogger : AuditLogger { override fun log(event: String) { writeToFile(event) } }
class NoOpAuditLogger : AuditLogger { override fun log(event: String) { } }
// Production wires FileAuditLogger, tests inject NoOpAuditLogger
```

</pattern>

---

<pattern id="AP5">

## 5. Mocking concrete classes

**Pillar damaged:** Resistance to refactoring, maintainability  
**Why it happens:** Want to stub one method while keeping the rest of the class real.

The need to partially mock a concrete class signals an SRP violation. Split the class: one for domain logic (testable directly), one for external communication (mockable via interface).

```kotlin
// ❌ Partial mock of concrete class — hides the design problem
val stub = spyk(StatisticsCalculator()) {
    every { getDeliveries(any()) } returns emptyList()  // must be virtual
}

// ✅ Split responsibilities
class DeliveryGateway : IDeliveryGateway {
    override fun getDeliveries(customerId: String): List<DeliveryRecord> { /* calls API */ }
}
class StatisticsCalculator {
    fun calculate(records: List<DeliveryRecord>): Stats { /* pure logic */ }
}
// Test StatisticsCalculator directly; mock IDeliveryGateway in integration tests
```

</pattern>

---

<pattern id="AP6">

## 6. Asserting stub interactions (mock/stub confusion)

**Pillar damaged:** Resistance to refactoring  
**Why it happens:** Using `verify` on a mock that was only there to provide input data.

A **stub** provides incoming data and should never be verified; a **mock** captures outgoing side effects and should always be verified. Asserting a stub was called couples the test to the SUT's internal call sequence, not its outcome.

```kotlin
// ❌ Asserting interaction with a stub (provides data, not a side effect)
val repo = mockk<UserRepository>()
coEvery { repo.findById("1") } returns user
val result = sut.getUser("1")
coVerify { repo.findById("1") }  // ← anti-pattern: this is a stub, not a mock

// ✅ Assert the outcome, not the plumbing
result shouldBe user

// ✅ Only verify mocks — dependencies that produce side effects
val emailGateway = mockk<EmailGateway>()
coEvery { emailGateway.send(any()) } just Runs
sut.notifyUser("1")
coVerify(exactly = 1) { emailGateway.send(match { it.to == "user@example.com" }) }
```

</pattern>

---

<pattern id="AP7">

## 7. Testing implementation details (brittle tests)

**Pillar damaged:** Resistance to refactoring  
**Why it happens:** White-box testing — test was written by reading the source code.

Tests should verify observable behavior from the end user's perspective, not the internal steps the SUT takes. If a refactoring that preserves behavior breaks the test, the test was wrong.

```kotlin
// ❌ Brittle: asserts internal structure, not behavior
test("renderer uses correct sub-renderers") {
    val sut = MessageRenderer()
    sut.subRenderers.size shouldBe 3
    sut.subRenderers[0].shouldBeInstanceOf<HeaderRenderer>()
    sut.subRenderers[1].shouldBeInstanceOf<BodyRenderer>()
}
// Breaks if you rename BodyRenderer or add a renderer, even if output is identical

// ✅ Resilient: asserts observable output
test("renders message as HTML") {
    val sut = MessageRenderer()
    sut.render(Message(header = "h", body = "b", footer = "f")) shouldBe
        "<h1>h</h1><b>b</b><i>f</i>"
}
```

</pattern>

---

<pattern id="AP8">

## 8. Time as ambient context

**Pillar damaged:** Protection against regressions (non-deterministic), maintainability  
**Why it happens:** `LocalDateTime.now()` is convenient.

Hidden time dependencies make tests non-deterministic (act phase time ≠ assert phase time) and introduce shared state between tests. Inject time explicitly as a value (preferred) or service.

```kotlin
// ❌ Hidden non-deterministic dependency
class AuditService {
    fun record(event: String) = AuditEntry(event, timestamp = LocalDateTime.now())
}
// Test can't control what "now" is

// ✅ Inject as a plain value — easiest to test
class AuditService {
    fun record(event: String, now: LocalDateTime) = AuditEntry(event, timestamp = now)
}

// ✅ Inject as interface when DI framework requires it
interface Clock { val now: LocalDateTime }
class SystemClock : Clock { override val now get() = LocalDateTime.now() }
class FixedClock(override val now: LocalDateTime) : Clock  // used in tests
```

</pattern>

---

<pattern id="AP9">

## 9. Multiple acts in a unit test

**Pillar damaged:** Fast feedback, maintainability  
**Why it happens:** Trying to test a sequence as one test.

Multiple act sections mean the test verifies multiple behaviors — it's an integration test at best, or a test that's hard to diagnose when it fails. Split into separate tests, one per action.

```kotlin
// ❌ Two acts in one test — which one broke?
test("purchase flow") {
    sut.addToCart(product)
    cart.items shouldContain product   // first assert

    sut.checkout(cart)                 // second act
    cart.status shouldBe CartStatus.CheckedOut
}

// ✅ Split — clear failure point
test("adding product puts it in cart") { ... }
test("checkout marks cart as checked out") { ... }
```

</pattern>

---

<pattern id="AP10">

## 10. Trivial tests (tautology)

**Pillar damaged:** Protection against regressions (zero value, just noise)  
**Why it happens:** Chasing coverage numbers.

A trivial test covers code with no branching and no domain significance — it can't catch a real bug and adds noise and maintenance cost.

```kotlin
// ❌ Tautology — tests nothing meaningful
test("user name is set") {
    val user = User(id = "1", name = "Alice")
    user.name shouldBe "Alice"
}

// ❌ Assertion-free — always passes
test("saving user does not throw") {
    sut.save(user)  // no assertion — coverage without protection
}
```

</pattern>

</anti-patterns>

---

## Audit script

Run `python scripts/audit_tests.py <path>` to scan for the patterns above. Each finding includes
file, line, severity, and the anti-pattern number from this list.

<constraints>
- Never verify stubs (AP6). Only verify mocks (outgoing effects).
- Never expose state (AP2) or internals (AP7) for tests — test observable output.
- Never compute expected values from inputs (AP3) — hard-code them.
- Never add isTestEnvironment flags to production code (AP4) — use interfaces.
- Tests with no assertion (AP10) must be deleted, not kept.
</constraints>
