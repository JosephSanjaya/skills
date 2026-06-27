# Ktor Server Guidelines

## Server Engines & Sizing
- **Netty**: Default/recommended for production. HTTP/2, EventLoop.
- **Tomcat / Jetty**: Servlet 3.0+ async.
- **CIO**: HTTP/1.1 only. Only choice for Native/GraalVM server targets. Do not use for HTTP/2.
- **Tuning EventLoop**:
  - `callGroupSize` = parallelism (CPU cores)
  - `connectionGroupSize` = `parallelism / 2 + 1`
  - `workerGroupSize` = `parallelism / 2 + 1`

## Dependency Injection (ktor-server-di)
- First-party DI module starting from Ktor 3.2.0. Avoids reflection overhead.
- **Import Path**: Always import from `io.ktor.server.plugins.di.dependencies` (not `io.ktor.server.di.dependencies`).
- Declare dependencies in module setup:
```kotlin
dependencies {
    provide<Logger> { Logger(printStreamProvider()) }
    provide<UserService>(::UserService)
}
// Property injection from application.conf/yaml
fun provideDB(@Property("database.url") url: String) = DB(url)
```
- Resolve dependencies inside Route or Application scopes:
```kotlin
// Direct resolution
val service = dependencies.resolve<UserService>()
// Lazy resolution via property delegation
val service: UserService by dependencies
```

## HTMX Integration (Experimental)
- Enabled via `ktor-server-htmx` plugin. Opt-in with `@OptIn(ExperimentalKtorApi::class)`.
- Use HTML DSL to output HTMX attributes and handle requests:
```kotlin
routing {
    get("/search") {
        val htmxRequest = call.request.headers.contains(HttpHeaders.HXRequest)
        if (htmxRequest) {
            call.respondHtml {
                body {
                    div {
                        attributes["hx-target"] = "#results"
                        +"Search Results Content"
                    }
                }
            }
        }
    }
}
```

## Configuration Deserialization
- In Ktor 3.5.0+, map full `ApplicationConfig` structure to single data class:
```kotlin
@Serializable
data class AppConfig(val db: DBConfig, val security: SecurityConfig)

fun Application.module() {
    val config = environment.config.getAs<AppConfig>()
    // ...
}
```
- **YAML Configuration Support**: To load from `application.yaml` instead of default HOCON (`application.conf`), you must explicitly add the config yaml dependency:
  `implementation("io.ktor:ktor-server-config-yaml-jvm:$ktorVersion")`

## Client Disconnect Cancellation
- Install `HttpRequestLifecycle` plugin to propagate cancellation to coroutine scope when client closes connection.
- Note: Only Netty and CIO support this; Servlet engines cannot reliably detect client disconnect.
- Cooperative cancellation: must check `isActive` or catch `CancellationException`.
```kotlin
install(HttpRequestLifecycle) {
    cancelCallOnClose = true
}
```

## WebSockets Backpressure & Sessions
- Avoid broadcasting to unsynchronized `Set` of sessions (concurrency bugs, zombie connections).
- Heartbeats: configure `pingPeriod` / `timeout` to clear dead connections.
- Backpressure: flow suspension naturally halts producer if consumer is slow.
- Prefer Server-Sent Events (SSE) over WebSockets if client only needs read-only updates.
