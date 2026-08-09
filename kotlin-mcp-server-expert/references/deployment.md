# Production Deployment of Kotlin MCP Servers

## Ktor Integration

The SDK ships `mcp {}` (SSE, deprecated) and `mcpStreamableHttp {}`. Use Streamable HTTP for all new deployments.

### Full production setup

```kotlin
import io.ktor.server.cio.CIO
import io.ktor.server.engine.embeddedServer
import io.ktor.server.routing.*
import io.ktor.server.response.*
import io.modelcontextprotocol.kotlin.sdk.server.mcpStreamableHttp

fun main() {
    embeddedServer(CIO, host = "127.0.0.1", port = 8080) {
        routing {
            get("/health") { call.respondText("ok") }
            get("/health/ready") {
                if (dependencies.allHealthy()) call.respondText("ok")
                else call.respond(HttpStatusCode.ServiceUnavailable, "not ready")
            }
            mcpStreamableHttp(path = "/mcp") { buildMyMcpServer() }
        }
    }.start(wait = true)
}
```

### Server factory pattern

The factory lambda in `mcpStreamableHttp {}` runs once per connection — correct for session isolation:

```kotlin
mcpStreamableHttp(path = "/mcp") {
    Server(
        serverInfo = Implementation("my-server", buildVersion()),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools     = ServerCapabilities.Tools(listChanged = true),
                resources = ServerCapabilities.Resources(listChanged = true),
                logging   = ServerCapabilities.Logging,
            )
        )
    ).apply { registerAllTools(this, serviceLocator) }
}
```

If your server is stateless (all state in DB/cache), you can share one instance — ensure handlers are thread-safe.

## Health Checks

| Endpoint | Purpose | Responds |
|---|---|---|
| `/health` | Liveness — is the process alive? | 200 always |
| `/health/ready` | Readiness — can we handle traffic? | 200 / 503 |

Readiness should check: DB connection, external API availability, MCP server init.

## Observability

### Structured logging

```kotlin
server.addTool("my_tool", "...", inputSchema) { request ->
    val start = System.currentTimeMillis()
    try {
        val result = doWork(request)
        logger.info { "tool=my_tool status=success duration_ms=${System.currentTimeMillis() - start}" }
        result
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        logger.error(e) { "tool=my_tool status=error duration_ms=${System.currentTimeMillis() - start} error=${e.message}" }
        CallToolResult(content = listOf(TextContent("Error: ${e.message}")), isError = true)
    }
}
```

### OpenTelemetry tracing

```kotlin
val tracer = GlobalOpenTelemetry.getTracer("mcp-server")

server.addTool("traced_tool", "...", inputSchema) { request ->
    val span = tracer.spanBuilder("mcp.tool.traced_tool").startSpan()
    try {
        span.makeCurrent().use {
            val result = doWork(request)
            span.setStatus(StatusCode.OK)
            result
        }
    } finally {
        span.end()
    }
}
```

Key spans: `mcp.session.initialize`, `mcp.tool.<name>`, external API calls within handlers.

### Web dashboard & runtime config

See [web-dashboard.md](web-dashboard.md) — MCP Inspector, SSE event feed, browser-editable `MutableStateFlow<ServerConfig>`.

### Alert thresholds (from production survey of 300+ MCP servers)
- Handshake success rate < 99% → Critical
- Tool error rate > 5% → High (check tool descriptions + input validation)
- P95 tool latency > 10s → Medium (check external API performance)

## Containerisation

```dockerfile
FROM gradle:8.5-jdk21 AS builder
WORKDIR /app
COPY . .
RUN gradle shadowJar --no-daemon

FROM gcr.io/distroless/java21-debian12:nonroot
WORKDIR /app
COPY --from=builder /app/build/libs/*-all.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

Key practices:
- Non-root user (distroless `nonroot` tag)
- Secrets via environment variables at runtime, not baked into image
- Scan with Trivy/Docker Scout in CI

## Horizontal Scaling

**Stateless** (recommended): load balancer, no session affinity.

**Stateful** (if using `Mcp-Session-Id`): consistent hashing in nginx:

```nginx
upstream mcp_servers {
    hash $http_mcp_session_id consistent;
    server mcp-1:8080;
    server mcp-2:8080;
    server mcp-3:8080;
}
```

Move session state to Redis for multi-instance persistence.

## Gradle Dependencies

```toml
[versions]
kotlin  = "2.1.0"
ktor    = "3.1.0"
mcp-sdk = "0.5.0"    # pin exact — ecosystem moves fast

[libraries]
mcp-sdk-server            = { module = "io.modelcontextprotocol:kotlin-sdk-server", version.ref = "mcp-sdk" }
ktor-server-cio           = { module = "io.ktor:ktor-server-cio", version.ref = "ktor" }
ktor-server-call-logging  = { module = "io.ktor:ktor-server-call-logging", version.ref = "ktor" }
```

Always verify the SDK version supports your target MCP spec version before upgrading.
