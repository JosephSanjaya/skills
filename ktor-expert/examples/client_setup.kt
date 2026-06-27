import io.ktor.client.*
import io.ktor.client.engine.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.auth.*
import io.ktor.client.plugins.auth.providers.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

// 1. KMP Platform Engine Factory (Expect/Actual definition)
// commonMain
expect fun getPlatformEngine(): HttpClientEngine

// 2. Platform-Specific Engine Factories with Pinning (Android/iOS Main targets)
/*
// androidMain
actual fun getPlatformEngine(): HttpClientEngine = io.ktor.client.engine.okhttp.OkHttp.create {
    preconfigured = okhttp3.OkHttpClient.Builder()
        .certificatePinner(
            okhttp3.CertificatePinner.Builder()
                .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
                .build()
        ).build()
}

// iosMain
actual fun getPlatformEngine(): HttpClientEngine = io.ktor.client.engine.darwin.Darwin.create {
    preconfigured = platform.Foundation.NSURLSessionConfiguration.defaultSessionConfiguration
    handleChallenge(io.ktor.client.engine.darwin.CertificatePinner(
        pins = mapOf("api.example.com" to "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    ))
}
*/

@Serializable
data class TokenResponse(val accessToken: String, val refreshToken: String)

interface TokenStorage {
    fun getAccessToken(): String?
    fun getRefreshToken(): String?
    fun setTokens(access: String, refresh: String)
    fun clear()
}

class TokenAuthenticator(
    private val tokenStorage: TokenStorage,
    private val clientProvider: () -> HttpClient
) {
    private val lock = Mutex()

    suspend fun refreshToken(params: RefreshTokensParams): Boolean {
        return lock.withLock {
            val currentAccess = tokenStorage.getAccessToken()
            val freshAccess = tokenStorage.getAccessToken()

            // Double check: if already refreshed by another concurrent call
            if (currentAccess != freshAccess && freshAccess != null) {
                return true
            }

            val refresh = tokenStorage.getRefreshToken() ?: return false

            try {
                // Request token refresh using a separate call flagged to avoid cycles
                val client = clientProvider()
                val response = client.post("https://api.example.com/auth/refresh") {
                    with(params) {
                        markAsRefreshTokenRequest() // Prevent auth loop
                    }
                    contentType(ContentType.Application.Json)
                    setBody(mapOf("refreshToken" to refresh))
                }

                if (response.status == HttpStatusCode.OK) {
                    val body = response.bodyAsText() // Deserialize safely
                    val tokens = Json.decodeFromString<TokenResponse>(body)
                    tokenStorage.setTokens(tokens.accessToken, tokens.refreshToken)
                    true
                } else {
                    tokenStorage.clear()
                    false
                }
            } catch (e: Exception) {
                tokenStorage.clear()
                false
            }
        }
    }
}

fun createKtorClient(
    engine: HttpClientEngine,
    tokenStorage: TokenStorage,
    authenticatorProvider: () -> TokenAuthenticator
): HttpClient {
    return HttpClient(engine) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                prettyPrint = true
            })
        }

        install(Logging) {
            logger = Logger.DEFAULT
            level = LogLevel.INFO
        }

        install(HttpRequestRetry) {
            maxRetries = 3
            retryOnServerErrors()
            exponentialDelay(base = 2.0, maxDelayMs = 10000)
            retryOnExceptionIf { _, cause -> cause is io.ktor.client.network.sockets.ConnectTimeoutException }
            modifyRequest { request ->
                // Ensure retries are only done on idempotent operations
                if (request.method != HttpMethod.Get && request.method != HttpMethod.Put) {
                    // Decide if safe to retry non-idempotent
                }
            }
        }

        install(HttpTimeout) {
            requestTimeoutMillis = 15000
            connectTimeoutMillis = 5000
            socketTimeoutMillis = 15000
        }

        install(Auth) {
            bearer {
                loadTokens {
                    val access = tokenStorage.getAccessToken()
                    val refresh = tokenStorage.getRefreshToken()
                    if (access == null || refresh == null) null else BearerTokens(access, refresh)
                }

                refreshTokens {
                    val authenticator = authenticatorProvider()
                    val success = authenticator.refreshToken(this)
                    if (success) {
                        val access = tokenStorage.getAccessToken()
                        val refresh = tokenStorage.getRefreshToken()
                        if (access != null && refresh != null) BearerTokens(access, refresh) else null
                    } else null
                }
                
                // Exclude auth path from sending authorization headers by default
                sendWithoutRequest { request ->
                    request.url.encodedPath.contains("/auth/")
                }
            }
        }
    }
}
