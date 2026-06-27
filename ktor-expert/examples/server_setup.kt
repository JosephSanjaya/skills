import io.ktor.server.application.*
import io.ktor.server.config.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.di.dependencies
import io.ktor.server.plugins.di.Property
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.http.HttpRequestLifecycle
import io.ktor.server.routing.*
import io.ktor.server.response.*
import io.ktor.http.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.Serializable

@Serializable
data class DatabaseConfig(val url: String, val poolSize: Int)

@Serializable
data class ServerAppConfig(
    val port: Int,
    val development: Boolean,
    val db: DatabaseConfig
)

class UserService(private val dbUrl: String) {
    fun fetchUserData(): String = "Data from database: $dbUrl"
}

fun main() {
    embeddedServer(Netty, port = 8080) {
        module()
    }.start(wait = true)
}

fun Application.module() {
    // 1. Root configuration deserialization (Ktor 3.5.0+)
    val config = environment.config.getAs<ServerAppConfig>()

    // 2. Configure first-party dependency injection (ktor-server-di)
    dependencies {
        provide<UserService> {
            UserService(config.db.url)
        }
    }

    // 3. Client disconnect cancellation plugin (Ktor 3.4.0+)
    install(HttpRequestLifecycle) {
        cancelCallOnClose = true
    }

    // 4. Secure exception mapping (prevent package structure leaks on type mismatches)
    install(StatusPages) {
        exception<io.ktor.server.plugins.BadRequestException> { call, cause ->
            // Log full exception internally, but return clean message to the client
            call.application.log.error("Bad Request: ${cause.message}", cause)
            call.respond(HttpStatusCode.BadRequest, mapOf("error" to "Invalid request payload format"))
        }
        exception<Throwable> { call, cause ->
            call.application.log.error("Internal Server Error", cause)
            call.respond(HttpStatusCode.InternalServerError, mapOf("error" to "An unexpected error occurred"))
        }
    }

    routing {
        // Resolve dependency inside routing block using property delegation
        val userService: UserService by dependencies

        get("/user-data") {
            val data = userService.fetchUserData()
            call.respond(mapOf("status" to "success", "data" to data))
        }

        // Safe, cancellation-aware route handler
        get("/long-task") {
            try {
                // Perform cooperative async processing
                var count = 0
                while (count < 10 && coroutineContext.isActive) {
                    delay(1000)
                    count++
                }
                call.respondText("Finished background work successfully")
            } catch (e: CancellationException) {
                // Safely handles when client disconnects mid-request
                application.log.info("Client cancelled the request. Cleaning up resources.")
                throw e
            }
        }
    }
}
