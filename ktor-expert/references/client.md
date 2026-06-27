# Ktor Client Guidelines

## Engine Matrix
- **OkHttp**: JVM/Android only. Support HTTP/2, pooling, GZIP. Best for Android production.
- **Darwin**: iOS/macOS. Wraps NSURLSession. VPN, ATS, backgrounding, proxy. Best for iOS production.
- **CIO**: Multiplatform. HTTP/1.1 only (no HTTP/2 multiplexing). Best for server-to-server, CLI, simple targets.

## Tuning CIO Pool
```kotlin
HttpClient(CIO) {
    engine {
        maxConnectionsCount = 1000
        endpoint {
            maxConnectionsPerRoute = 100
            pipelineMaxSize = 20
            keepAliveTime = 5000
            connectTimeout = 5000
        }
    }
}
```

## Token Refresh (Single-Flight & Mutex)
- Built-in `Auth` plugin bearer handles 401. Double-check lock with coroutine `Mutex` prevents concurrent calls.
- **Scope Limitation**: `markAsRefreshTokenRequest()` is a member function of `RefreshTokensParams` class. To call it in helper classes, pass `params: RefreshTokensParams` and scope it using `with(params) { markAsRefreshTokenRequest() }`.
- **Alternative (Universal)**: Manually put the `AuthCircuitBreaker` attribute in the request builder (requires `import io.ktor.client.plugins.auth.AuthCircuitBreaker`): `attributes.put(AuthCircuitBreaker, Unit)`.
- Avoid body-transformation reissue issues in 3.x (KTOR-9039).

```kotlin
class TokenAuthenticator(private val clientProvider: () -> HttpClient, private val storage: TokenStorage) {
    private val lock = Mutex()
    suspend fun refresh(params: RefreshTokensParams): Boolean = lock.withLock {
        val cur = storage.getAccess()
        val fresh = storage.getAccess()
        if (cur != fresh && fresh != null) return true
        val refresh = storage.getRefresh() ?: return false
        try {
            val client = clientProvider()
            val res = client.post("https://api.example.com/auth/refresh") {
                with(params) { markAsRefreshTokenRequest() }
                // OR: attributes.put(AuthCircuitBreaker, Unit)
                contentType(ContentType.Application.Json)
                setBody(mapOf("refreshToken" to refresh))
            }
            storage.setTokens(res.access, res.refresh)
            true
        } catch (e: Exception) {
            storage.clear()
            false
        }
    }
}
```

## Darwin/iOS Memory Leaks & Crashes
- **Retain Cycle**: NSURLSession retains delegate wrapper. Accessing tasks map triggers wrapper allocations.
- **WebSocket Leak**: Darwin does not auto-clear failed WebSockets. Must wrap `.ws` call in try-finally and call `close()`.
- **engine.close() Crash**: In-flight requests when Darwin engine closed throw uncatchable ObjC runtime exception → SIGABRT. Cancel requests before closing engine.
- **Tenant credentials**: Avoid sharing one HttpClient for distinct auth backends to prevent token leakage.

## KMP Platform Engine Factory (Expect/Actual)
- Define factory in commonMain and configure engine in target source sets.
```kotlin
// commonMain
expect fun createHttpClientEngine(): HttpClientEngine

// androidMain
actual fun createHttpClientEngine(): HttpClientEngine = OkHttp.create {
    // OkHttp specific configuration
}

// iosMain
actual fun createHttpClientEngine(): HttpClientEngine = Darwin.create {
    // Darwin specific configuration
}
```

## Platform-Specific Certificate Pinning
- **Android (OkHttp)**: Configure pinning directly on OkHttpClient.
```kotlin
OkHttp.create {
    preconfigured = OkHttpClient.Builder()
        .certificatePinner(
            CertificatePinner.Builder()
                .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
                .build()
        ).build()
}
```
- **iOS (Darwin)**: Pin certificates via Darwin `CertificatePinner`.
```kotlin
Darwin.create {
    preconfigured = NSURLSessionConfiguration.defaultSessionConfiguration
    // Use Darwin CertificatePinner for hostname-scoped pinning
    handleChallenge(CertificatePinner(
        pins = mapOf("api.example.com" to "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    ))
}
```

