---
name: testing-expert
description: "Ultimate Kotlin testing skill. Use this whenever writing, reviewing, or debugging ANY Kotlin test — unit, integration, property-based, or coroutine. Covers TDD (RED/GREEN/REFACTOR), Kotest + MockK + Kover, anti-pattern detection, and four-pillar quality framework. Triggers on: write a test, add coverage, why is this test fragile, should I test this, how do I mock X, is this a good test, audit my tests, refactor this test, or any task involving Kotlin test files."
origin: unit-testing-book + kotlin-testing + kotlin-test skills
---

# Testing Expert — Kotlin

The **only goal** of unit testing is sustainable project growth. Every decision below serves that goal.

## Quick decision guide

<quick-ref>
**Should I write this test?**
→ Read [`references/four-pillars.md`](references/four-pillars.md) — code categories section.

| Code type | Action |
|---|---|
| Domain logic / algorithms (complex, few collaborators) | ✅ Unit test thoroughly |
| Trivial (constructor, one-liner property) | ⛔ Skip — no regression protection |
| Controller / orchestration | 🔬 Brief integration test |
| Overcomplicated (complex + many collaborators) | 🔴 Refactor with Humble Object first |

**Is my test fragile / breaking on refactor?**
→ It's coupled to implementation details, not observable behavior. See [`references/four-pillars.md`](references/four-pillars.md) — resistance to refactoring.

**How do I structure a test?**
→ AAA below. For Kotest/MockK patterns: [`references/kotlin-tools.md`](references/kotlin-tools.md).

**Should I use a mock here?**
→ [`references/mocking-discipline.md`](references/mocking-discipline.md).

**Is this an anti-pattern?**
→ Run the audit script or see [`references/anti-patterns.md`](references/anti-patterns.md).
</quick-ref>

---

## TDD: The non-negotiable cycle

<tdd-cycle>
```
RED    → Write a failing test that describes the behavior
GREEN  → Write the minimum code to pass it
REFACTOR → Improve under green tests
REPEAT
```

Never skip RED. A test that passes before implementation either tests the wrong thing or nothing.

```kotlin
// 1. Define signature only
fun validateEmail(email: String): Result<String> = TODO()

// 2. Write test FIRST — it fails with NotImplementedError (RED confirmed)
class EmailValidatorTest : StringSpec({
    "blank email is rejected" { validateEmail("").shouldBeFailure() }
    "valid email is accepted" { validateEmail("user@example.com").shouldBeSuccess() }
})

// 3. Implement minimum code (GREEN) → 4. Refactor
```
</tdd-cycle>

---

## AAA structure (every test)

<aaa>
```kotlin
test("confirmed order reduces inventory") {
    // Arrange — bring SUT and dependencies to desired state
    val inventory = Inventory(sku = "SKU-1", quantity = 10)
    val sut = OrderService(inventory)

    // Act — one line; if it's two lines, the SUT API has an encapsulation problem
    sut.placeOrder(OrderRequest(sku = "SKU-1", quantity = 3))

    // Assert — verify observable outcome, not internal steps
    inventory.available("SKU-1") shouldBe 7
}
```

**AAA rules:**
- One act per test. Two acts = split into two tests.
- No `if` in tests. Branch = two separate tests.
- Name the SUT `sut` to make it stand out from dependencies.
- Reuse setup via private factory methods, not constructors/`beforeTest` shared state (that couples tests).
</aaa>

---

## Test naming

<naming>
Name tests as plain English facts, not rigid patterns.

| ❌ Rigid (brittle, programmer-only) | ✅ Plain English fact |
|---|---|
| `validateEmail_nullInput_ReturnsFalse` | `blank email is rejected` |
| `isDeliveryValid_PastDate_ReturnsFalse` | `delivery with a past date is invalid` |
| `purchase_succeeds_when_enough_inventory` | `purchase reduces inventory on success` |

Rules: no method name in test name, use underscores for long names, state facts not wishes
("is invalid" not "should be invalid").
</naming>

---

## Anti-pattern quick checklist

<anti-patterns>
Run `scripts/audit_tests.py <path>` to detect automatically. Full explanations with Kotlin
examples in [`references/anti-patterns.md`](references/anti-patterns.md).

| # | Anti-pattern | Signal |
|---|---|---|
| 1 | Testing private methods directly | Exposed internal via `internal` just for tests |
| 2 | Exposing private state for assertions | Public getter that only tests use |
| 3 | Leaking domain knowledge | `expected = value1 + value2` in test |
| 4 | Code pollution | `isTestEnvironment` flag in production class |
| 5 | Mocking concrete classes | `spyk(ConcreteClass())` overriding one method |
| 6 | Asserting stub interactions | `coVerify` on a `coEvery` that only provided data |
| 7 | Testing implementation details | Asserting internal structure, not output |
| 8 | Time as ambient context | `LocalDate.now()` hidden inside production method |
| 9 | Multiple acts in one unit test | Second act without a separate test |
| 10 | Trivial tests (tautology) | Tests that can never fail |
</anti-patterns>

---

## Kotlin toolchain

<toolchain>
For full patterns and runnable examples, read the relevant section:

- **Kotest spec styles + matchers** → [`references/kotlin-tools.md#kotest`](references/kotlin-tools.md)
- **MockK setup, stubs, mocks, capture, coroutines** → [`references/kotlin-tools.md#mockk`](references/kotlin-tools.md)
- **Coroutine testing (runTest, advanceTimeBy, Flows)** → [`references/kotlin-tools.md#coroutines`](references/kotlin-tools.md)
- **Property-based testing (forAll, checkAll, Arb)** → [`references/kotlin-tools.md#property`](references/kotlin-tools.md)
- **Data-driven tests (withData)** → [`references/kotlin-tools.md#data-driven`](references/kotlin-tools.md)
- **Kover coverage config** → [`references/kotlin-tools.md#kover`](references/kotlin-tools.md)

```bash
./gradlew test                        # run all tests
./gradlew test --tests "com.example.UserServiceTest"
./gradlew koverHtmlReport             # coverage report
./gradlew koverVerify                 # fail build if below threshold
python scripts/audit_tests.py src/    # scan for anti-patterns
```
</toolchain>

---

## Deeper theory

When you need to reason about test quality or architecture:

- **Four pillars + code categories + test pyramid** → [`references/four-pillars.md`](references/four-pillars.md)
- **Mock vs stub, when to mock, classical school** → [`references/mocking-discipline.md`](references/mocking-discipline.md)
- **All anti-patterns with Kotlin examples** → [`references/anti-patterns.md`](references/anti-patterns.md)

<constraints>
- Never assert on stubs (coEvery for data = stub, never coVerify it).
- One act per test. Two acts = two tests.
- Expected values hard-coded, never computed from inputs.
- No LocalDateTime.now() hidden in production code — inject time.
- Resistance to refactoring is non-negotiable: verify outcomes not steps.
</constraints>
