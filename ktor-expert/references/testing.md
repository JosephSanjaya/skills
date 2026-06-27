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
