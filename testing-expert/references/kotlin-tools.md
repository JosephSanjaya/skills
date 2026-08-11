# Kotlin Testing Tools Reference

## Table of Contents
- [Kotest spec styles](#kotest-spec-styles)
- [Kotest matchers](#kotest-matchers)
- [MockK](#mockk)
- [Coroutine testing](#coroutine-testing)
- [Property-based testing](#property-based-testing)
- [Data-driven tests](#data-driven-tests)
- [Test lifecycle and fixtures](#test-lifecycle-and-fixtures)
- [Kover coverage](#kover-coverage)

---

<kotest-specs>

## Kotest spec styles

Pick one style per project and stay consistent.

### StringSpec — flat, simple
```kotlin
class CalculatorTest : StringSpec({
    "adds two positive numbers" { Calculator.add(2, 3) shouldBe 5 }
    "adds negative numbers" { Calculator.add(-1, -2) shouldBe -3 }
    "adding zero is identity" { Calculator.add(0, 5) shouldBe 5 }
})
```

### FunSpec — JUnit-like, good for service tests
```kotlin
class UserServiceTest : FunSpec({
    val repo = mockk<UserRepository>()
    val sut = UserService(repo)

    test("returns user when found") {
        coEvery { repo.findById("1") } returns User("1", "Alice")
        sut.getUser("1").name shouldBe "Alice"
    }

    test("throws when not found") {
        coEvery { repo.findById("999") } returns null
        shouldThrow<UserNotFoundException> { sut.getUser("999") }
    }
})
```

### BehaviorSpec — BDD / Given-When-Then
```kotlin
class OrderServiceTest : BehaviorSpec({
    val paymentGateway = mockk<PaymentGateway>()
    val sut = OrderService(paymentGateway)

    Given("a valid order") {
        val order = Order(sku = "SKU-1", quantity = 2)

        When("payment succeeds") {
            coEvery { paymentGateway.charge(any()) } returns ChargeResult.Success

            Then("order is confirmed") {
                sut.place(order).status shouldBe OrderStatus.CONFIRMED
            }
            Then("payment is charged once") {
                coVerify(exactly = 1) { paymentGateway.charge(any()) }
            }
        }

        When("payment fails") {
            coEvery { paymentGateway.charge(any()) } returns ChargeResult.Declined

            Then("throws PaymentException") {
                shouldThrow<PaymentException> { sut.place(order) }
            }
        }
    }
})
```

### DescribeSpec — RSpec style, good for validators
```kotlin
class UserValidatorTest : DescribeSpec({
    val sut = UserValidator()

    describe("validate") {
        context("valid input") {
            it("accepts normal user") {
                sut.validate(CreateUserRequest("Alice", "alice@example.com")).shouldBeValid()
            }
        }
        context("invalid name") {
            it("rejects blank name") {
                sut.validate(CreateUserRequest("", "alice@example.com")).shouldBeInvalid()
            }
            it("rejects name over 255 chars") {
                sut.validate(CreateUserRequest("A".repeat(256), "alice@example.com")).shouldBeInvalid()
            }
        }
    }
})
```

</kotest-specs>

---

<kotest-matchers>

## Kotest matchers

```kotlin
// Equality
result shouldBe expected
result shouldNotBe unexpected

// Strings
name shouldStartWith "Al"
name shouldEndWith "ce"
name shouldContain "lic"
name shouldMatch Regex("[A-Z][a-z]+")
name.shouldBeBlank()
name.shouldNotBeBlank()

// Collections
list shouldContain "item"
list shouldHaveSize 3
list.shouldBeEmpty()
list.shouldNotBeEmpty()
list.shouldContainAll("a", "b", "c")
list.shouldBeSorted()

// Nulls
result.shouldBeNull()
result.shouldNotBeNull()

// Types
result.shouldBeInstanceOf<User>()

// Numbers
count shouldBeGreaterThan 0
count shouldBeLessThan 100
price shouldBeInRange 1.0..100.0

// Exceptions
shouldThrow<IllegalArgumentException> {
    validateAge(-1)
}.message shouldBe "Age must be positive"

shouldNotThrow<Exception> {
    validateAge(25)
}

// Result<T>
result.shouldBeSuccess()
result.shouldBeFailure()
result.shouldBeSuccess("expected value")

// Custom matcher
fun beActiveUser() = object : Matcher<User> {
    override fun test(value: User) = MatcherResult(
        value.isActive && value.lastLogin != null,
        { "User ${value.id} should be active with a last login" },
        { "User ${value.id} should not be active" },
    )
}
user should beActiveUser()
```

</kotest-matchers>

---

<mockk>

## MockK

See [`mocking-discipline.md`](mocking-discipline.md) for when to use mocks vs stubs.

```kotlin
val repo = mockk<UserRepository>()
val logger = mockk<Logger>(relaxed = true)  // relaxed: don't set up every call

// Stubs (incoming data — setup only, never verify)
every { repo.findById("1") } returns user
coEvery { repo.findById("1") } returns user       // suspend
every { config.timeout } returns Duration.seconds(30)

// Mocks (outgoing side effects — always verify after act)
coEvery { emailGateway.send(any()) } just Runs
every { auditLog.record(any()) } just Runs

// Verify mocks
coVerify(exactly = 1) { emailGateway.send(match { it.to == "alice@example.com" }) }
coVerify(exactly = 0) { emailGateway.send(any()) }  // assert NOT called
confirmVerified(emailGateway)                        // fail if unexpected calls remain

// Argument capture
val slot = slot<User>()
coEvery { repo.save(capture(slot)) } returns Unit
sut.register(CreateUserRequest("Alice", "alice@example.com"))
slot.captured.name shouldBe "Alice"
slot.captured.email shouldBe "alice@example.com"

// Dynamic answers
coEvery { repo.findById(any()) } coAnswers { User(firstArg(), "stub") }

// Spy — real object with one method overridden
val realService = UserService(repo)
val spy = spyk(realService)
every { spy.generateId() } returns "fixed-id"
spy.createUser(request)
verify { spy.generateId() }  // the overridden method

// Lifecycle
beforeTest { clearMocks(repo, emailGateway) }
```

</mockk>

---

<coroutine-testing>

## Coroutine testing

```kotlin
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.StandardTestDispatcher

class CoroutineServiceTest : FunSpec({

    test("suspend function completes") {
        runTest {
            val result = sut.fetchData()
            result.shouldNotBeNull()
        }
    }

    test("timeout cancels slow operation") {
        runTest {
            shouldThrow<TimeoutCancellationException> {
                withTimeout(100) { sut.slowOperation() }
            }
        }
    }

    test("debounce fires only for final input") {
        runTest {
            val queries = MutableSharedFlow<String>()
            val results = mutableListOf<List<Item>>()
            val job = launch { sut.search(queries).collect { results.add(it) } }

            queries.emit("a")
            queries.emit("ab")
            queries.emit("abc")
            advanceTimeBy(500)  // skip real time — never use Thread.sleep()

            results shouldHaveSize 1
            job.cancel()
        }
    }

    test("controlled dispatcher execution order") {
        val dispatcher = StandardTestDispatcher()
        runTest(dispatcher) {
            var completed = false
            launch {
                delay(1000)
                completed = true
            }
            completed shouldBe false
            advanceTimeBy(1000)
            completed shouldBe true
        }
    }
})
```

</coroutine-testing>

---

<property-testing>

## Property-based testing

```kotlin
import io.kotest.property.Arb
import io.kotest.property.arbitrary.*
import io.kotest.property.forAll
import io.kotest.property.checkAll

class PropertyTest : FunSpec({

    test("string reverse is involutory") {
        forAll<String> { s -> s.reversed().reversed() == s }
    }

    test("list sort is idempotent") {
        forAll(Arb.list(Arb.int())) { list ->
            list.sorted() == list.sorted().sorted()
        }
    }

    test("serialization roundtrip preserves data") {
        checkAll(
            Arb.string(1..50),
            Arb.string(5..20).map { "$it@example.com" },
        ) { name, email ->
            val user = User(name = name, email = email)
            Json.decodeFromString<User>(Json.encodeToString(user)) shouldBe user
        }
    }
})

// Custom generators
val userArb = Arb.bind(
    Arb.string(minSize = 1, maxSize = 50),
    Arb.email(),
    Arb.enum<Role>(),
) { name, email, role -> User(name = name, email = email, role = role) }

val moneyArb = Arb.bind(
    Arb.long(1L..1_000_000L),
    Arb.enum<Currency>(),
) { amount, currency -> Money(amount, currency) }
```

</property-testing>

---

<data-driven>

## Data-driven tests

```kotlin
class ParserTest : FunSpec({
    context("valid dates") {
        withData(
            "2026-01-15" to LocalDate(2026, 1, 15),
            "2026-12-31" to LocalDate(2026, 12, 31),
        ) { (input, expected) ->
            parseDate(input) shouldBe expected
        }
    }

    context("invalid dates are rejected") {
        withData(
            nameFn = { "rejects '$it'" },
            "not-a-date", "2026-13-01", "2026-00-15", "",
        ) { input ->
            shouldThrow<DateParseException> { parseDate(input) }
        }
    }
})
```

</data-driven>

---

<lifecycle>

## Test lifecycle and fixtures

```kotlin
class DatabaseTest : FunSpec({
    lateinit var db: Database

    beforeSpec {
        db = Database.connect("jdbc:h2:mem:test;DB_CLOSE_DELAY=-1")
        SchemaUtils.create(UsersTable)
    }

    afterSpec {
        SchemaUtils.drop(UsersTable)
    }

    beforeTest {
        UsersTable.deleteAll()  // reset state — each test independent
    }

    test("insert and retrieve user") {
        UsersTable.insert { it[name] = "Alice"; it[email] = "alice@example.com" }
        UsersTable.selectAll().map { it[UsersTable.name] } shouldContain "Alice"
    }
})
```

For shared infrastructure (DB connection) across many test classes, use a base class:

```kotlin
abstract class IntegrationTestBase : FunSpec() {
    protected val db = Database.connect("jdbc:h2:mem:test;DB_CLOSE_DELAY=-1")
    init { beforeSpec { SchemaUtils.create(UsersTable) } }
}
class UserRepositoryTest : IntegrationTestBase() { ... }
```

</lifecycle>

---

<kover>

## Kover coverage

```kotlin
// build.gradle.kts
plugins { id("org.jetbrains.kotlinx.kover") version "0.9.7" }

kover {
    reports {
        filters {
            excludes { classes("*.generated.*", "*.di.*", "*.config.*", "*BuildConfig*") }
        }
        verify {
            rule { minBound(80) }  // fail build below 80% — adjust per project
        }
    }
}
```

```bash
./gradlew koverHtmlReport   # open build/reports/kover/html/index.html
./gradlew koverVerify       # CI gate
./gradlew koverXmlReport    # for Codecov / SonarQube
```

Coverage is a **negative indicator**: low = definitely a problem, high = not necessarily good.
Don't mandate a specific number — see four-pillars.md.

</kover>

<constraints>
- Never Thread.sleep() in coroutine tests — use advanceTimeBy/advanceUntilIdle.
- Stub repositories with coEvery; never coVerify them.
- One Kotest spec style per project — pick and stay consistent.
- Kover: coverage is a negative indicator only — low = problem, high ≠ quality.
</constraints>
