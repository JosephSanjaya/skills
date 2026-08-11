# Four Pillars of a Good Test

## The four pillars

<pillars>

Every test scores on these dimensions. A zero in any one makes the test worthless (multiply rule).

| Pillar | What it measures | How to maximize |
|---|---|---|
| **Protection against regressions** | Can this test catch real bugs? | Exercise more code, focus on domain logic + complexity |
| **Resistance to refactoring** | Does the test stay green during refactors that don't change behavior? | Verify *outcomes*, not *steps*; black-box the SUT |
| **Fast feedback** | Does it run fast enough to run on every change? | No out-of-process deps in unit tests |
| **Maintainability** | Is it easy to read and keep operational? | Short tests, no flaky deps, clear names |

**Resistance to refactoring is non-negotiable.** It's binary — you have it or you don't.
Trade-offs are always between fast feedback and regression protection, never at the expense of refactoring resistance.

**False positives** (test fails, behavior correct) result from coupling to implementation details — eroding suite trust until developers ignore all failures.

**False negatives** (test passes, bug exists) result from insufficient coverage or missing assertions.

</pillars>

---

## Code categories — what to test

<code-categories>

Plot every class/method on this grid before writing tests:

```
                        FEW COLLABORATORS          MANY COLLABORATORS
                       ┌────────────────────────┬──────────────────────────┐
HIGH COMPLEXITY /      │  Domain model +        │  Overcomplicated          │
DOMAIN SIGNIFICANCE    │  Algorithms            │  (fat controller,         │
                       │                        │   Active Record pattern)  │
                       │  ✅ UNIT TEST HEAVILY  │  🔴 REFACTOR FIRST        │
                       ├────────────────────────┼──────────────────────────┤
LOW COMPLEXITY /       │  Trivial code          │  Controllers /            │
DOMAIN SIGNIFICANCE    │  (constructors,        │  Orchestration            │
                       │   simple properties)   │  (glue code only)         │
                       │  ⛔ DON'T TEST         │  🔬 INTEGRATION TEST      │
                       └────────────────────────┴──────────────────────────┘
```

### Domain model + algorithms (top-left)
High complexity + few collaborators = best regression ROI.
```kotlin
// Good candidate: business logic, no out-of-process deps
class PriceCalculator {
    fun calculateDiscount(products: List<Product>): Double {
        val discount = products.size * 0.01
        return minOf(discount, 0.20)
    }
}
```

### Trivial code (bottom-left)
No branching, no domain significance = near-zero bug probability and zero regression protection.
```kotlin
// Don't test — no logic
data class User(val id: String, val name: String)
class UserFactory { fun create(id: String, name: String) = User(id, name) }
```

### Controllers / orchestration (bottom-right)
Orchestrates domain + out-of-process deps. Integration tests only; skip unit tests.
```kotlin
class UserController(private val db: Database, private val bus: MessageBus) {
    fun changeEmail(userId: String, newEmail: String): String {
        val user = db.getUser(userId)
        user.changeEmail(newEmail)   // all logic lives in User, not here
        db.save(user)
        bus.publish(EmailChangedEvent(userId, newEmail))
        return "OK"
    }
}
```

### Overcomplicated code (top-right) — split with Humble Object
Domain class coupled to DB or message bus. Apply Humble Object: extract logic into a collaborator-free class, leave the original as thin coordinator.

```kotlin
// ❌ Before: User reaches out to DB and bus directly (overcomplicated)
class User {
    fun changeEmail(newEmail: String) {
        val data = Database.getUser(id)  // out-of-process in domain!
        // ... logic ...
        MessageBus.publish(...)
    }
}

// ✅ After: separate domain logic from orchestration
class User {
    fun changeEmail(newEmail: String, company: Company) {
        // pure logic, no out-of-process deps
    }
}
class UserController {
    fun changeEmail(userId: String, newEmail: String) {
        val user = db.getUser(userId)     // orchestration only
        val company = db.getCompany()
        user.changeEmail(newEmail, company)
        db.save(user)
        bus.publish(user.domainEvents)
    }
}
```

**Rule: the more important or complex the code, the fewer collaborators it should have.**

</code-categories>

---

## The Test Pyramid

<pyramid>

```
          /\
         /E2E\          few — slow, expensive, cover only critical paths
        /──────\
       / Integ  \       moderate — controller + real managed deps (DB, filesystem)
      /────────────\
     /  Unit Tests  \   many — fast, cheap, cover domain model + algorithms
    /────────────────\
```

- Unit tests: domain + algorithms — many, fast, no out-of-process deps
- Integration tests: controller + real DB (mock only unmanaged: external APIs, payment, email)
- E2E: only most critical user journeys — very few

Coverage is a **negative indicator only**: low = definitely a problem; high = not necessarily good. Never mandate a number.

</pyramid>

---

## Three testing styles

<testing-styles>

| Style | Verify | Best for |
|---|---|---|
| **Output-based** (functional) | Return value only | Pure functions, algorithms |
| **State-based** | SUT or collaborator state after action | Domain classes with in-memory side effects |
| **Communication-based** | Interactions with mocks | Calls to unmanaged out-of-process deps |

Prefer output-based. Fall back to state-based. Use communication-based only at the app boundary.

</testing-styles>

---

## Coverage targets (guide, not mandate)

<coverage>

| Code type | Target |
|---|---|
| Critical business logic | 100% |
| Public API surface | 90%+ |
| General domain code | 80%+ |
| Controllers / generated / config | Exclude or skip |

</coverage>

<constraints>
- Resistance to refactoring is non-negotiable: binary, never trade away.
- Overcomplicated code (top-right): refactor with Humble Object before testing.
- Trivial code (bottom-left): do not test — zero regression protection.
- Coverage is a negative indicator only — never mandate a number.
- Test pyramid: many unit, moderate integration, few E2E.
</constraints>
