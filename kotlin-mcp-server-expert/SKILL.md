---
name: kotlin-mcp-server-expert
description: "Expert guidance for building production-grade MCP (Model Context Protocol) servers in Kotlin using the official Kotlin Multiplatform SDK. Use this skill whenever the user is building, designing, debugging, or improving an MCP server in Kotlin — including tool registration, resource templates, prompt handling, transport selection (stdio vs Streamable HTTP), coroutine patterns, structured output, error handling, token efficiency, security, testing, and deployment. Trigger even if the user only mentions \"MCP\", \"kotlin sdk mcp\", \"addTool\", \"CallToolResult\", \"ServerCapabilities\", or is wiring up a Ktor-based MCP server. Also trigger for questions like \"how do I build an AI tool server in Kotlin\", \"expose my API as MCP tools\", or \"wire up Claude to my Kotlin backend\"."
---

# Kotlin MCP Server Expert

Build production-grade MCP servers in Kotlin — idiomatic, coroutine-native, efficient.

## Decision Tree: Where to Start

| Your situation | Go to |
|---|---|
| First server / minimal setup | [Quick Start](#quick-start) |
| Choosing transport (stdio vs HTTP) | [Transport Selection](#transport-selection) |
| Designing tools / resources / prompts | [references/primitives.md](references/primitives.md) |
| Coroutine patterns in handlers | [references/coroutines.md](references/coroutines.md) |
| Error handling & isError protocol | [references/error-handling.md](references/error-handling.md) |
| Token efficiency & response design | [references/token-efficiency.md](references/token-efficiency.md) |
| Security hardening | [references/security.md](references/security.md) |
| Testing (unit + integration) | [references/testing.md](references/testing.md) |
| Production / Ktor deployment | [references/deployment.md](references/deployment.md) |
| Web dashboard / MCP Inspector / SSE live feed / browser config | [references/web-dashboard.md](references/web-dashboard.md) |

---

## Quick Start

### Minimal stdio server
```kotlin
import io.ktor.utils.io.streams.asSource
import io.ktor.utils.io.streams.asSink
import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.server.StdioServerTransport
import io.modelcontextprotocol.kotlin.sdk.types.*

fun main() {
    val server = Server(
        serverInfo = Implementation(name = "my-server", version = "1.0.0"),
        options = ServerOptions(
            capabilities = ServerCapabilities(
                tools = ServerCapabilities.Tools(listChanged = true)
            )
        )
    )

    server.addTool(
        name = "greet",
        description = "Greet a user by name. Returns a personalised greeting.",
        inputSchema = ToolSchema(
            properties = buildJsonObject {
                put("name", buildJsonObject {
                    put("type", "string")
                    put("description", "The user's name")
                })
            },
            required = listOf("name")
        )
    ) { request ->
        val name = request.arguments?.get("name")?.jsonPrimitive?.content
            ?: return@addTool CallToolResult(
                content = listOf(TextContent("Missing required argument: name")),
                isError = true
            )
        CallToolResult(content = listOf(TextContent("Hello, $name!")))
    }

    val transport = StdioServerTransport(
        inputStream = System.`in`.asSource().buffered(),
        outputStream = System.out.asSink().buffered()
    )
    // createSession suspends until transport closes — run in runBlocking or a coroutine scope
    runBlocking { server.createSession(transport) }
}
```

### Minimal Streamable HTTP server (Ktor)
```kotlin
import io.ktor.server.cio.CIO
import io.ktor.server.engine.embeddedServer
import io.modelcontextprotocol.kotlin.sdk.server.mcpStreamableHttp

fun main() {
    embeddedServer(CIO, host = "127.0.0.1", port = 3000) {
        mcpStreamableHttp {
            buildMyServer()   // returns a configured Server instance
        }
    }.start(wait = true)
}
```

---

## Transport Selection

| Criterion | stdio | Streamable HTTP |
|---|---|---|
| Deployment | Local subprocess | Remote / cloud |
| Sessions | Single-tenant | Multi-tenant |
| Auth | Process-level | Bearer / OAuth 2.1 |
| Scaling | Single instance | Horizontal (stateless) |
| Cold start | Microseconds | Milliseconds |
| Preferred for | CLI, IDE plugins | Cloud APIs, SaaS |

**Rule:** use stdio for local dev and tooling. Use Streamable HTTP (via Ktor `mcpStreamableHttp`) for anything deployed remotely. Avoid the legacy SSE transport — it's deprecated.

---

## ServerCapabilities: Declare What You Support

Only declare capabilities you actually register handlers for — the SDK enforces this at runtime.

```kotlin
ServerCapabilities(
    tools     = ServerCapabilities.Tools(listChanged = true),       // server.addTool(...)
    resources = ServerCapabilities.Resources(
        subscribe   = true,   // clients may subscribe to resource changes
        listChanged = true    // server emits notifications/resources/list_changed
    ),
    prompts   = ServerCapabilities.Prompts(listChanged = true),
    logging   = ServerCapabilities.Logging,                         // sendLoggingMessage(...)
)
```

---

## Core API Cheatsheet

```kotlin
// Tools
server.addTool(name, description, inputSchema, outputSchema?) { req -> CallToolResult(...) }

// Resources (static URI)
server.addResource(uri, name, description, mimeType) { req -> ReadResourceResult(...) }

// Resources (URI templates, e.g. "repo://{owner}/{repo}/file/{path}")
server.addResourceTemplate(uriTemplate, name, description, mimeType) { req -> ReadResourceResult(...) }

// Prompts
server.addPrompt(name, description, arguments?) { req -> GetPromptResult(...) }

// Notify clients of dynamic changes (from ClientConnection receiver)
sendToolListChanged()
sendResourceListChanged()
sendLoggingMessage(LoggingMessageNotification(...))

// Lifecycle hooks
server.onConnect { /* runs on each new session */ }
```

All handlers are `suspend` lambdas with `ClientConnection` as the receiver — giving direct access to `sendLoggingMessage`, `sendToolListChanged`, etc. from inside a handler.

---

## Five Rules You Must Not Break

1. **Never write to stdout in stdio mode.** stdout is the JSON-RPC wire. Use `System.err` or `sendLoggingMessage` for all diagnostics.
2. **Always validate arguments before use.** Return `CallToolResult(isError = true)` for bad input — never throw from a handler for expected user errors.
3. **Rethrow `CancellationException`.** Catching `Exception` in a coroutine handler swallows cancellation. Catch only specific types, or catch then rethrow `CancellationException`.
4. **Declare capabilities before adding primitives.** `addTool` throws `IllegalStateException` if `tools` capability is absent from `ServerOptions`.
5. **One server instance per transport connection.** Never share mutable server state across concurrent HTTP connections — the SDK handles session isolation, but you must not use shared mutable state in handlers.

---

## Reference Index

- **[primitives.md](references/primitives.md)** — Deep guide: tool design, inputSchema, outputSchema, structured output, resource templates, prompts, tool annotations, response content types.
- **[coroutines.md](references/coroutines.md)** — Dispatcher selection, structured concurrency in handlers, Flow integration, progress notifications, avoiding deadlocks.
- **[error-handling.md](references/error-handling.md)** — `isError` vs exceptions, retry patterns, partial failures, business errors vs protocol errors.
- **[token-efficiency.md](references/token-efficiency.md)** — Response verbosity, pagination, ResourceLink, field projection, capping output.
- **[security.md](references/security.md)** — Input validation, SSRF prevention, command injection, OAuth 2.1, secret management, sandboxing.
- **[testing.md](references/testing.md)** — ChannelTransport unit tests, runTest patterns, integration tests, assertion strategies.
- **[deployment.md](references/deployment.md)** — Ktor integration, health checks, observability, horizontal scaling, containerisation.
- **[web-dashboard.md](references/web-dashboard.md)** — MCP Inspector, SSE live event feed, browser-editable runtime config (`MutableStateFlow<ServerConfig>`).
- **[niche-edge-cases.md](references/niche-edge-cases.md)** — Dynamic tool registration, elicitation, sampling, Tasks API, cancellation, protocol version, multi-tenant isolation.
