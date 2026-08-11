# Mocking Discipline

<mock-vs-stub>

## Mock vs Stub — the critical distinction

| Type | Direction | Action | Verify? |
|---|---|---|---|
| **Stub** | Incoming — provides input data TO the SUT | `coEvery { repo.findById(id) } returns user` | **Never** |
| **Mock** | Outgoing — SUT causes a side effect on it | `coEvery { emailGateway.send(any()) } just Runs` | **Always** |

**Never assert interactions with stubs.** A stub is an implementation detail; refactor data fetching → test breaks for no reason.

```kotlin
// ❌ Stub assertion — anti-pattern
val repo = mockk<UserRepository>()
coEvery { repo.findById("1") } returns User("1", "Alice")
sut.getUser("1")
coVerify { repo.findById("1") }  // don't do this

// ✅ Assert the outcome
val result = sut.getUser("1")
result.name shouldBe "Alice"

// ✅ Mock: verify the outgoing side effect
val bus = mockk<MessageBus>()
coEvery { bus.publish(any()) } just Runs
sut.changeEmail("1", "new@example.com")
coVerify(exactly = 1) { bus.publish(ofType<EmailChangedEvent>()) }
```

</mock-vs-stub>

---

<when-to-mock>

## When to mock

### ✅ Mock: unmanaged out-of-process dependencies
External systems the test team doesn't control: payment gateways, third-party APIs, email services,
SMS providers. Interactions with these ARE observable behavior — they cross the application boundary.

```kotlin
val paymentGateway = mockk<PaymentGateway>()
coEvery { paymentGateway.charge(any()) } returns ChargeResult.Success
// ... act ...
coVerify(exactly = 1) { paymentGateway.charge(match { it.amount == 99.99 }) }
```

### ✅ Mock / stub: volatile or slow dependencies in unit tests
Random number generators, system clock (prefer injection as value — see anti-patterns #8),
services that require network access. Replace with stubs in unit tests, use real ones in
integration tests.

### ❌ Don't mock: managed out-of-process dependencies (your own DB)
Your own database is an implementation detail. Test against the real thing — mocking masks real ORM/query bugs.

```kotlin
// ❌ Mocking your own DB in a unit test — misses real ORM/query bugs
val db = mockk<Database>()
coEvery { db.save(any()) } just Runs

// ✅ Integration test with real DB (H2 in-memory or TestContainers)
class UserRepositoryTest : FunSpec({
    val db = Database.connect("jdbc:h2:mem:test;DB_CLOSE_DELAY=-1")
    beforeSpec { SchemaUtils.create(UsersTable) }
    afterSpec { SchemaUtils.drop(UsersTable) }
    beforeTest { UsersTable.deleteAll() }

    test("saves and retrieves user") {
        val repo = UserRepository(db)
        repo.save(User("1", "Alice"))
        repo.findById("1")?.name shouldBe "Alice"
    }
})
```

### ❌ Don't mock: data classes / value objects
They're immutable and interchangeable. Just use real instances.

```kotlin
// ❌ Unnecessary mock of a value object
val product = mockk<Product> { every { price } returns 10.0 }

// ✅ Use the real thing
val product = Product(sku = "SKU-1", price = 10.0)
```

### ❌ Don't mock: in-process domain collaborators
Calls between domain classes are implementation details — verify state, not interactions.

```kotlin
// ❌ Mocking a domain collaborator — brittle
val company = mockk<Company>()
every { company.isEmailCorporate(any()) } returns true
user.changeEmail("new@corp.com", company)
verify { company.isEmailCorporate("new@corp.com") }  // tests steps, not outcome

// ✅ Use real Company, assert final state
val company = Company(domain = "corp.com", employeeCount = 5)
user.changeEmail("new@corp.com", company)
user.type shouldBe UserType.Employee
company.employeeCount shouldBe 6
```

### ❌ Don't mock concrete classes
See anti-patterns #5. Split the class instead.

</when-to-mock>

---

<classical-school>

## Classical school (preferred)

Isolate **tests from each other**, not classes from each other. Two tests must not share mutable
state (static fields, DB rows written by one test and read by another).

Use mocks only for shared or out-of-process dependencies; test domain clusters with real collaborators.

**London school** (avoid as default) — mock every collaborator; use only when the object graph is truly unwieldy.

</classical-school>

---

<mockk-ref>

## MockK quick reference

```kotlin
// Setup
val repo = mockk<UserRepository>()               // strict mock
val logger = mockk<Logger>(relaxed = true)        // relaxed: returns defaults

// Stubs (incoming — don't verify)
every { repo.findById("1") } returns user
every { repo.findById(any()) } returns null
coEvery { repo.findById("1") } returns user       // suspend functions
every { repo.findById(any()) } throws NotFoundException()

// Mocks (outgoing — verify after act)
coEvery { emailGateway.send(any()) } just Runs

// Verify (mocks only)
verify(exactly = 1) { repo.save(any()) }
coVerify(exactly = 0) { emailGateway.send(any()) }
coVerify { bus.publish(ofType<EmailChangedEvent>()) }

// Argument capture
val slot = slot<User>()
coEvery { repo.save(capture(slot)) } returns Unit
// ... act ...
slot.captured.name shouldBe "Alice"

// Answer (dynamic return value)
coEvery { repo.findById(any()) } coAnswers { User(firstArg(), "dynamic") }

// Lifecycle
beforeTest { clearMocks(repo, logger) }
```

</mockk-ref>

<constraints>
- Stub = incoming data: setup with coEvery, NEVER coVerify.
- Mock = outgoing side effect: setup with coEvery just Runs, ALWAYS coVerify.
- Own DB = managed dep: use real H2/TestContainers, never mock.
- Data classes = value objects: use real instances, never mock.
- spyk(ConcreteClass()) = SRP violation signal: split the class instead.
</constraints>
