# Niche & Edge Cases for Kotlin MCP Servers

## Dynamic Tool Registration

Add tools at runtime and notify connected clients. Declare `listChanged = true` in capabilities:

```kotlin
server.addTool("activate_category", "Load an additional tool category", inputSchema) { request ->
    val category = request.arguments!!["category"]!!.jsonPrimitive.content
    when (category) {
        "admin" -> registerAdminTools(server)
        "analytics" -> registerAnalyticsTools(server)
        else -> return@addTool CallToolResult(
            content = listOf(TextContent("Unknown category: $category. Available: admin, analytics")),
            isError = true
        )
    }
    sendToolListChanged()  // fires notifications/tools/list_changed to all sessions
    CallToolResult(content = listOf(TextContent("Activated category: $category")))
}
```

**Why this matters:** Every tool's schema is injected into the model's context. Lazy-loading keeps context lean.

## Protocol Version

The SDK negotiates protocol version during `initialize`. Streamable HTTP also validates `MCP-Protocol-Version` header per request:

```kotlin
// StreamableHttpServerTransport.validateProtocolVersion() handles this automatically.
// Supported older versions are accepted; unknown future versions return HTTP 400.
// You don't need to implement this — just keep the SDK up to date.
```

If you see `400 Unsupported protocol version` in the wild: check that your client and server SDK versions are compatible.

## Elicitation (Mid-call User Input)

The server can pause a tool call and ask the user for structured input (requires the client to declare `elicitation` capability):

```kotlin
// Elicitation is available via ClientConnection.requestElicitation()
// Check ClientCapabilities.elicitation before calling
server.addTool("create_ticket", "Create a support ticket", inputSchema) { request ->
    val title = request.arguments?.get("title")?.jsonPrimitive?.contentOrNull
    if (title == null) {
        // Request input from the user (not the model)
        val elicited = requestElicitation(
            ElicitRequest(
                message = "Please provide a title for the ticket:",
                requestedSchema = ElicitRequest.Schema(
                    properties = buildJsonObject { put("title", buildJsonObject { put("type", "string") }) },
                    required = listOf("title")
                )
            )
        )
        when (elicited.action) {
            "accept"  -> processTicket(elicited.content!!["title"]!!.jsonPrimitive.content)
            "decline" -> return@addTool CallToolResult(content = listOf(TextContent("Cancelled.")))
            "cancel"  -> return@addTool CallToolResult(content = listOf(TextContent("Cancelled.")))
            else      -> return@addTool CallToolResult(content = listOf(TextContent("Unknown action.")), isError = true)
        }
    }
    processTicket(title!!)
}
```

**Use URL mode for credentials** — the SDK sends the user to a URL to enter secrets, so your server never handles them.

## Sampling (Server-side LLM calls)

The server can ask the **client** to run an LLM completion (requires client capability):

```kotlin
// Available via ClientConnection.createMessage()
server.addTool("summarise_doc", "Summarise a document using the connected LLM", inputSchema) { request ->
    val doc = loadDocument(request.arguments!!["docId"]!!.jsonPrimitive.content)

    val samplingResult = createMessage(
        CreateMessageRequest(
            messages = listOf(
                SamplingMessage(Role.user, TextContent("Summarise this document in 3 bullet points:\n\n$doc"))
            ),
            maxTokens = 500,
            modelPreferences = ModelPreferences(hints = listOf(ModelHint("claude-sonnet")))
        )
    )

    CallToolResult(content = listOf(TextContent((samplingResult.content as TextContent).text)))
}
```

Useful for agent loops where the server orchestrates LLM calls without holding API keys.

## Tasks (Async Long-Running Operations)

The Tasks API (experimental, shipped 2025-11-25, being redesigned into an extension for 2026-07-28) allows long-running tools to return a handle and let the client poll:

```kotlin
// ponytail: Tasks API is still experimental — code against it cautiously.
// States: working / input_required / completed / failed / cancelled
// Check the SDK changelog before depending on this in production.
```

For now, simulate async with progress notifications via `sendLoggingMessage` + polling tools.

## Multi-Tenant Session Isolation

In Streamable HTTP mode, multiple clients connect concurrently. Never share mutable state between sessions:

```kotlin
// WRONG — shared mutable map across sessions
private val sessionData = mutableMapOf<String, String>()

// CORRECT — use the session ID from the MCP-Session-Id header, or scope state to the coroutine scope of each handler
mcpStreamableHttp(path = "/mcp") {
    // Each call to this block creates a fresh Server instance — good isolation
    Server(/* ... */).apply {
        // All per-session state is stack-local or in the handler's coroutine scope
        val perSessionCache = ConcurrentHashMap<String, String>()
        addTool("query", "...", inputSchema) { req ->
            // perSessionCache is captured per-factory invocation — isolated per connection
            val cached = perSessionCache[req.arguments!!["key"]!!.jsonPrimitive.content]
            // ...
        }
    }
}
```

## Handling Concurrent Tool Calls

Multiple tool calls can arrive concurrently from the same client. The SDK dispatches each to a coroutine — ensure your tools are safe to run in parallel:

```kotlin
// If tools share a DB connection pool: use HikariCP or similar pooling — it's already thread-safe
// If tools share a rate-limit counter: use AtomicInteger
// If tools share a cache: use ConcurrentHashMap<K, V>
// If tools need serialised writes: use Dispatchers.IO.limitedParallelism(1) for that section

private val writeLimiter = Dispatchers.IO.limitedParallelism(1)

server.addTool("safe_write", "...", inputSchema) { request ->
    withContext(writeLimiter) {
        db.write(/* ... */)
    }
    CallToolResult(content = listOf(TextContent("Written.")))
}
```

## Graceful Shutdown

For stdio servers, handle `SIGTERM`:

```kotlin
Runtime.getRuntime().addShutdownHook(Thread {
    runBlocking {
        server.close()
    }
})
```

For Ktor servers, Ktor handles graceful shutdown automatically when `wait = true` and a shutdown signal is received.

## stdio: The Stdout Trap

**In stdio mode, any write to stdout corrupts the JSON-RPC channel.** This includes:
- `println(...)` ← breaks the protocol
- `System.out.println(...)` ← breaks the protocol
- Logging frameworks configured to stdout ← breaks the protocol

Configure SLF4J / Logback to write exclusively to stderr or a file:

```xml
<!-- logback.xml for stdio MCP servers -->
<configuration>
    <appender name="STDERR" class="ch.qos.logback.core.ConsoleAppender">
        <target>System.err</target>
        <encoder><pattern>%d{HH:mm:ss} %-5level %logger - %msg%n</pattern></encoder>
    </appender>
    <root level="INFO"><appender-ref ref="STDERR"/></root>
</configuration>
```

Or use MCP's structured logging instead:

```kotlin
sendLoggingMessage(LoggingMessageNotification(
    LoggingMessageNotificationParams(level = LoggingLevel.Debug, logger = "my-server", data = buildJsonObject { put("msg", "startup complete") })
))
```

## Protocol Capability Mismatch

If a client sends `JSON-RPC -32602 Invalid params`, the most common cause is the server attempting to use a capability the client didn't declare (e.g., calling `requestElicitation` when the client declared no `elicitation` capability). Always guard:

```kotlin
// Check client capabilities before using advanced features
if (clientCapabilities.elicitation != null) {
    requestElicitation(/* ... */)
} else {
    // Fall back to requiring the argument in the tool input
}
```
