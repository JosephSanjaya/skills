# Error Handling in MCP Kotlin Servers

## The Two Error Channels

| Channel | When to use | How |
|---|---|---|
| `CallToolResult(isError = true)` | Expected user-facing errors (bad input, not found, API quota) | Return a result with an error message the model can act on |
| Exception / protocol error | Unexpected server bugs, missing capabilities | Let it propagate — the SDK returns JSON-RPC `-32603` |

**The model can self-correct from `isError = true` results** (e.g., "Invalid date format: use YYYY-MM-DD"). Protocol exceptions (-32602, -32603) are harder for the model to recover from — use them only for true server faults.

## Pattern: Guard-clause argument validation

Validate early, return `isError` for every constraint violation, with actionable messages:

```kotlin
server.addTool("create_issue", "Create a GitHub issue", inputSchema) { request ->
    val args = request.arguments
        ?: return@addTool CallToolResult(
            content = listOf(TextContent("No arguments provided")), isError = true)

    val title = args["title"]?.jsonPrimitive?.contentOrNull
    if (title.isNullOrBlank()) return@addTool CallToolResult(
        content = listOf(TextContent("title is required and must not be blank")), isError = true)

    if (title.length > 256) return@addTool CallToolResult(
        content = listOf(TextContent("title must be ≤ 256 characters (got ${title.length})")),
        isError = true)

    // happy path
    val issue = githubClient.createIssue(title = title)
    CallToolResult(content = listOf(TextContent("Created #${issue.number}: ${issue.url}")))
}
```

## Pattern: Wrapping external calls

Translate external service failures into actionable error results:

```kotlin
server.addTool("fetch_data", "...", inputSchema) { request ->
    val id = request.arguments!!["id"]!!.jsonPrimitive.content
    try {
        val data = withTimeout(15_000L) { apiClient.fetch(id) }
        CallToolResult(content = listOf(TextContent(data.toJson())))
    } catch (e: TimeoutCancellationException) {
        CallToolResult(
            content = listOf(TextContent("Request timed out after 15s. The service may be slow — try again shortly.")),
            isError = true
        )
    } catch (e: NotFoundException) {
        CallToolResult(
            content = listOf(TextContent("Item '$id' not found. Check the ID and try again.")),
            isError = true
        )
    } catch (e: RateLimitException) {
        CallToolResult(
            content = listOf(TextContent("Rate limit exceeded. Retry after ${e.retryAfterSeconds}s.")),
            isError = true
        )
    } catch (e: CancellationException) {
        throw e  // ALWAYS rethrow — breaks structured cancellation if swallowed
    } catch (e: Exception) {
        CallToolResult(
            content = listOf(TextContent("Unexpected error: ${e.message}")),
            isError = true
        )
    }
}
```

## Pattern: Partial success (batch tools)

When processing a list, return both successes and failures:

```kotlin
data class ItemResult(val id: String, val success: Boolean, val value: String? = null, val error: String? = null)

server.addTool("batch_delete", "Delete multiple records", inputSchema) { request ->
    val ids = request.arguments!!["ids"]!!.jsonArray.map { it.jsonPrimitive.content }

    val results = ids.map { id ->
        try {
            db.delete(id)
            ItemResult(id, success = true)
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            ItemResult(id, success = false, error = e.message)
        }
    }

    val succeeded = results.count { it.success }
    val failed = results.filter { !it.success }

    val summary = buildString {
        appendLine("Deleted $succeeded/${ids.size} records.")
        if (failed.isNotEmpty()) {
            appendLine("Failed:")
            failed.forEach { appendLine("  - ${it.id}: ${it.error}") }
        }
    }

    // Only set isError = true if ALL failed
    CallToolResult(
        content = listOf(TextContent(summary)),
        isError = succeeded == 0 && ids.isNotEmpty()
    )
}
```

## Structured Logging for Diagnostics

Send log notifications to the client (visible in MCP Inspector and Claude Code) rather than writing to stderr — except in stdio mode where `sendLoggingMessage` is the only safe channel:

```kotlin
sendLoggingMessage(LoggingMessageNotification(
    LoggingMessageNotificationParams(
        level  = LoggingLevel.Error,
        logger = "my-server.tool.fetch_data",
        data   = buildJsonObject {
            put("error",  e.message)
            put("itemId", id)
        }
    )
))
```

## Resource handler errors

For `addResource` / `addResourceTemplate`, throw a meaningful exception — the SDK translates it to a JSON-RPC error:

```kotlin
server.addResourceTemplate("file://{path}", "File", "Read a file", "text/plain") { request ->
    val path = extractPath(request.uri)
    val file = File(path).canonicalFile
    if (!file.exists()) throw NoSuchElementException("File not found: $path")
    ReadResourceResult(contents = listOf(TextResourceContents(file.readText(), request.uri, "text/plain")))
}
```
