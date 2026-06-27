# Ktor Testing Guidelines

## Unit Testing with MockEngine
- Intercept HTTP calls in-memory using `MockEngine`.
- Verifies headers, parameters, paths, body payloads.
```kotlin
val client = HttpClient(MockEngine) {
    install(ContentNegotiation) { json() }
    engine {
        addHandler { request ->
            when (request.url.encodedPath) {
                "/profile" -> respond(
                    content = ByteReadChannel("""{"name":"User"}"""),
                    status = HttpStatusCode.OK,
                    headers = headersOf(HttpHeaders.ContentType, "application/json")
                )
                else -> respond(
                    content = ByteReadChannel("""{"error":"Not Found"}"""),
                    status = HttpStatusCode.NotFound
                )
            }
        }
    }
}
```

## KMP MockEngine + Bearer Auth: Critical Pitfalls (Ktor 3.x)

These rules apply whenever you install the `Auth` plugin with `bearer {}` and test with `MockEngine` in a KMP context.

### 1. Disable `HttpTimeout` in test clients
`HttpTimeout` + `MockEngine` + auth retry can deadlock on native targets. Strip it in tests:
```kotlin
val testClient = HttpClient(MockEngine) {
    // Do NOT install HttpTimeout here
    install(Auth) {
        bearer {
            loadTokens { BearerTokens("access", "refresh") }
            refreshTokens {
                markAsRefreshTokenRequest()
                // perform refresh ...
                BearerTokens("new-access", "new-refresh")
            }
        }
    }
    engine { addHandler { request -> /* ... */ } }
}
```

### 2. Refresh client must use its own isolated `MockEngine`
The `Bearer` plugin's `refreshTokens` block fires a request on the **same** `HttpClient` if you don't separate engines. Use a dedicated `refreshHttpClient` backed by a separate `MockEngine`:
```kotlin
val refreshEngine = MockEngine { request ->
    // only handles /auth/refresh-token
    respond("""{ "access_token":"new", "refresh_token":"r" }""",
        HttpStatusCode.OK, headersOf(ContentType, "application/json"))
}
val refreshClient = HttpClient(refreshEngine) { install(ContentNegotiation) { json() } }
```

### 3. 401 responses must include `WWW-Authenticate: Bearer`
The Ktor `Auth` plugin only invokes `refreshTokens` when the 401 response carries this header. Without it the plugin skips refresh and propagates the error directly:
```kotlin
respond(
    content = ByteReadChannel("{\"error\":\"Unauthorized\"}"),
    status = HttpStatusCode.Unauthorized,
    headers = headersOf(
        HttpHeaders.ContentType to listOf("application/json"),
        HttpHeaders.WWWAuthenticate to listOf("Bearer realm=\"api\"")
    )
)
```

### 4. `sendWithoutRequest` — use `pathSegments` not `encodedPath`
For KMP (especially iOS native), prefer `pathSegments.contains("auth")` over `encodedPath.contains("auth")` to avoid percent-encoding inconsistencies:
```kotlin
bearerTokens {
    sendWithoutRequest { request ->
        !request.url.pathSegments.contains("auth")
    }
}
```

### 5. Reuse test doubles via a dedicated `:core:<domain>:testing` module
Instead of copying `FakePreferenceRepository` and `MockEngine` setup per module:
- Place `FakePreferenceRepository` and `NetworkMockServer` (factory object) in `commonMain` of `:core:network:testing`
- Declare `api(sjy.ktor.mock)` so `ktor-client-mock` is transitive to all consumers

## Integration Testing with testApplication
- Spins up sandboxed in-memory Ktor server.
- Test routing, middleware, plugins, database transactions.
- **Ktor Native DI Overrides**: Override dependencies before loading modules:
```kotlin
@Test
fun testProfileNativeDI() = testApplication {
    application {
        dependencies.provide<DB> { TestInMemoryDB() }
        configureRouting() // Loads routes that resolve DB
    }
    val client = createClient { install(ContentNegotiation) { json() } }
    val res = client.get("/profile")
    assertEquals(HttpStatusCode.OK, res.status)
}
```
- **Koin Overrides**:
```kotlin
@Test
fun testProfileKoin() = testApplication {
    application {
        install(Koin) {
            allowOverride(true)
            modules(module {
                single<DB> { TestInMemoryDB() }
            })
        }
        configureRouting()
    }
    val client = createClient { install(ContentNegotiation) { json() } }
    val res = client.get("/profile")
    assertEquals(HttpStatusCode.OK, res.status)
}
```

## Parallel Test Database Isolation
- Avoid shared state leaks when tests run in parallel.
- Run a single container database and programmatically provision isolated schemas/databases per test run (e.g., random schema name in PostgreSQL/H2) to keep startup overhead minimal.
